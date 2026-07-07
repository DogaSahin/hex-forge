// app/core/static/ws.js — Hexforge WS client. Envelope: {topic, action, payload}.
(function () {
  const handlers = {}; // action -> [fn]
  let socket = null;

  function connect(topic) {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${location.host}/ws?topic=${encodeURIComponent(topic || "broadcast")}`;
    socket = new WebSocket(url);
    socket.addEventListener("message", (ev) => {
      let msg;
      try {
        msg = JSON.parse(ev.data);
      } catch (_) {
        return;
      }
      const fns = handlers[msg.action] || [];
      fns.forEach((fn) => fn(msg.payload, msg));
    });
    return socket;
  }

  function subscribe(topic) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ topic, action: "subscribe", payload: {} }));
    }
  }

  function on(action, handler) {
    (handlers[action] = handlers[action] || []).push(handler);
  }

  window.HexWS = { connect, subscribe, on };
})();
