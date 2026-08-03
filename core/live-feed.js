window.SMILE = window.SMILE || (function(){
  let activeSymbol = "BTC/USDT";
  const listeners = {};
  const tickers = {
    "BTC/USDT": { symbol: "BTC/USDT", binance: "BTCUSDT", price: null, change: 0, candles: [], spark: [] },
    "ETH/USDT": { symbol: "ETH/USDT", binance: "ETHUSDT", price: null, change: 0, candles: [], spark: [] },
    "SOL/USDT": { symbol: "SOL/USDT", binance: "SOLUSDT", price: null, change: 0, candles: [], spark: [] },
    "BNB/USDT": { symbol: "BNB/USDT", binance: "BNBUSDT", price: null, change: 0, candles: [], spark: [] },
    "XRP/USDT": { symbol: "XRP/USDT", binance: "XRPUSDT", price: null, change: 0, candles: [], spark: [] }
  };

  function emit(event, data) {
    if (listeners[event]) listeners[event].forEach(fn => fn(data));
  }

  function on(event, fn) {
    listeners[event] = listeners[event] || [];
    listeners[event].push(fn);
  }

  function setActive(sym) {
    if (tickers[sym]) activeSymbol = sym;
    emit('smile:active', activeSymbol);
    fetchKlines();
  }

  async function fetchTicker() {
    try {
      const syms = Object.values(tickers).map(t => `"${t.binance}"`).join(',');
      const res = await fetch(`https://data-api.binance.vision/api/v3/ticker/24hr?symbols=[${syms}]`);
      const data = await res.json();
      data.forEach(item => {
        const match = Object.values(tickers).find(t => t.binance === item.symbol);
        if (match) {
          match.price = parseFloat(item.lastPrice);
          match.change = parseFloat(item.priceChangePercent);
          match.spark.push(match.price);
          if (match.spark.length > 50) match.spark.shift();
        }
      });
      broadcast();
    } catch (e) {
      const t = tickers[activeSymbol];
      if (t) {
        t.price = t.price || 95000.00;
        t.price += (Math.random() - 0.49) * 15;
        t.spark.push(t.price);
        if (t.spark.length > 50) t.spark.shift();
        broadcast();
      }
    }
  }

  async function fetchKlines() {
    const t = tickers[activeSymbol];
    if (!t) return;
    try {
      const res = await fetch(`https://data-api.binance.vision/api/v3/klines?symbol=${t.binance}&interval=1m&limit=60`);
      const data = await res.json();
      t.candles = data.map(c => [parseInt(c[0]), parseFloat(c[1]), parseFloat(c[2]), parseFloat(c[3]), parseFloat(c[4])]);
      broadcast();
    } catch (e) {
      t.candles = [];
    }
  }

  function broadcast() {
    const current = tickers[activeSymbol] || { symbol: activeSymbol, price: 0, change: 0, candles: [], spark: [] };
    emit('smile:chart', {
      sym: current.symbol,
      price: current.price,
      chg: current.change,
      candles: current.candles,
      spark: current.spark,
      ind: true
    });
  }

  function indicators(closes) {
    if (!closes || closes.length < 14) return { trend: 'RANGE', rsi: 50, cross: false };
    let gains = 0, losses = 0;
    for (let i = closes.length - 14; i < closes.length; i++) {
      const diff = closes[i] - closes[i - 1];
      if (diff >= 0) gains += diff; else losses -= diff;
    }
    const avgGain = gains / 14, avgLoss = losses / 14;
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    const rsi = 100 - (100 / (1 + rs));
    const last = closes[closes.length - 1], prev = closes[closes.length - 2];
    const trend = last > prev ? 'BULL' : (last < prev ? 'BEAR' : 'RANGE');
    return { trend, rsi, cross: last > prev };
  }

  setInterval(fetchTicker, 3000);
  setInterval(fetchKlines, 10000);
  setTimeout(() => { fetchTicker(); fetchKlines(); }, 200);

  return { on, setActive, indicators, getActive: () => activeSymbol };
})();