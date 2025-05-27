document.addEventListener("DOMContentLoaded", function () {
    const path = window.location.pathname;
    const username = path.split("/").pop();
    const ws = new WebSocket(`ws://${location.host}/ws/${username}`);

    const form = document.getElementById("chatForm");
    const input = document.getElementById("messageInput");
    const messages = document.getElementById("messages");
    const recipient = document.getElementById("recipient");

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const target = recipient.value;
        const msg = input.value;
        if (msg.trim() === "") return;
        ws.send(`${target}:${msg}`);
        const li = document.createElement("li");
        li.textContent = `${username}: ${msg}`;
        messages.appendChild(li);
        input.value = "";
    });

    ws.onmessage = function (event) {
        const li = document.createElement("li");
        li.textContent = event.data;
        messages.appendChild(li);
    };
});