//@version=5
strategy("Cloud Auto-Bracket Strategy", overlay=true, margin_long=0, margin_short=0, max_bars_back=500)

// --- Strategy Inputs ---
tp_ticks = input.int(60, title="Take Profit (Ticks)")
sl_ticks = input.int(40, title="Initial Stop Loss (Ticks)")
be_trigger_ticks = input.int(24, title="Profit Trigger for Breakeven (Ticks)")
be_plus_ticks = input.int(4, title="Breakeven Plus Offset (Ticks)")

// --- Indicators ---
source = close
bb_length = input.int(20, title="BB Length")
bb_mult = input.float(2.0, title="BB StdDev")
rsi_length = input.int(14, title="RSI Length")

[basis, upper, lower] = ta.bb(source, bb_length, bb_mult)
my_rsi = ta.rsi(source, rsi_length)

// --- FORCED LIVE TIME TRIGGER ---
// (timenow - time) tracks how close the bar is to your actual computer clock.
// This keeps the strategy completely empty historically, then flips to TRUE on the live candle.
is_live_candle = (timenow - time) < 300000 // Within the last 5 minutes

long_condition = false
short_condition = is_live_candle

// --- Trade Execution Logic ---
if (long_condition and strategy.position_size == 0)
    strategy.entry("buy", strategy.long, comment="buy")

if (short_condition and strategy.position_size == 0)
    strategy.entry("sell", strategy.short, comment="sell")

// --- Server-Side Advanced Exit Calculations ---
if (strategy.position_size > 0)
    entry_p = strategy.position_avg_price
    bars_since_entry = ta.barssince(strategy.position_size[1] == 0)
    
    safe_lookback = bars_since_entry > 0 ? math.min(bars_since_entry, 450) : 1
    highest_high = ta.highest(high, safe_lookback)
    ticks_in_profit = (highest_high - entry_p) / syminfo.mintick
    
    current_sl = entry_p - (sl_ticks * syminfo.mintick)
    if (ticks_in_profit >= be_trigger_ticks)
        current_sl := entry_p + (be_plus_ticks * syminfo.mintick)
        
    strategy.exit("close", "buy", limit=entry_p + (tp_ticks * syminfo.mintick), stop=current_sl, comment="close")

if (strategy.position_size < 0)
    entry_p = strategy.position_avg_price
    bars_since_entry = ta.barssince(strategy.position_size[1] == 0)
    
    safe_lookback = bars_since_entry > 0 ? math.min(bars_since_entry, 450) : 1
    lowest_low = ta.lowest(low, safe_lookback)
    ticks_in_profit = (entry_p - lowest_low) / syminfo.mintick
    
    current_sl = entry_p + (sl_ticks * syminfo.mintick)
    if (ticks_in_profit >= be_trigger_ticks)
        current_sl := entry_p - (be_plus_ticks * syminfo.mintick)
        
    strategy.exit("close", "sell", limit=entry_p - (tp_ticks * syminfo.mintick), stop=current_sl, comment="close")
