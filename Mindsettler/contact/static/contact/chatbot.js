const input = document.getElementById("chat-input");
const chatBox = document.getElementById("chat-box");

input.addEventListener("keypress", function (e) {
    if (e.key === "Enter" && input.value.trim() !== "") {
        const msg = input.value;

        chatBox.innerHTML += `<p><b>You:</b> ${msg}</p>`;
        input.value = "";

        fetch("/contact/chatbot/api/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg })
        })
        .then(res => res.json())
        .then(data => {
            chatBox.innerHTML += `<p><b>Bot:</b> ${data.reply}</p>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        });
    }
});
