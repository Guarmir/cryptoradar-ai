async function getScore() {
    const coin = document.getElementById("coin").value.toLowerCase();
    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "⏳ Buscando...";

    try {
        const response = await fetch(
            `https://cryptoradar-ai.onrender.com/score/${coin}`
        );
        const data = await response.json();

        if (data.error) {
            resultDiv.innerHTML = "⚠️ " + data.error;
            return;
        }

        resultDiv.innerHTML = `
            <p><strong>${coin.toUpperCase()}</strong></p>
            <p>Preço: $${data.price_usd}</p>
            <p>Score: <strong>${data.score}</strong></p>
            <p>${data.signal}</p>
        `;
    } catch (e) {
        resultDiv.innerHTML = "❌ Erro ao conectar com a API";
    }
}
