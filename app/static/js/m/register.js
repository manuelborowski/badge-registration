$(document).ready(async () => {
    // test rfid
    document.getElementById("repair-new-btn").addEventListener("click", async () => {
        const out = document.getElementById("search-input");
        try {
            const ndef = new NDEFReader();
            await ndef.scan();
            out.value = "> Scan started" +  (new Date()).toString();

            ndef.addEventListener("readingerror", () => {
                console.log("Argh! Cannot read data from the NFC tag. Try another one?");
            });

            ndef.addEventListener("reading", ({message, serialNumber}) => {
                console.log(`> Serial Number: ${serialNumber}`);
                console.log(`> Records: (${message.records.length})`)
                out.value = serialNumber;
            });
        } catch (error) {
            out.value = "Argh! " + error;
        }
        document.getElementById("repair-new-btn").hidden = true;

    });
});
