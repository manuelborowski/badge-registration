$(document).ready(async () => {
    const register_type_select = document.getElementById("register-type-select");
    const main = document.getElementById("main");
    const register_list = document.getElementById("register-list");
    const out = document.getElementById("log-out");
    const clear_list_button = document.getElementById("clear-list-btn");

    const ret = await fetch(Flask.url_for('register.meta'));
    const meta = await ret.json();

    const register_type_options = [{label: "Selecteer een type", value: null}, {label: "TEST", value: "test"}].concat(meta.locations);
    register_type_options.forEach(l => register_type_select.add(new Option(l.label, l.value, false, false)));

    let ndef = null;

    const registration_cache = JSON.parse(localStorage.getItem("registrations")) || {};

    register_type_select.addEventListener("change", async (e) => {
        if (["null", "test"].includes(e.target.value)) {
            main.classList.add("register-not-active");
            main.classList.remove("register-active");
        } else {
            main.classList.remove("register-not-active");
            main.classList.add("register-active");
        }
        if (e.target.value in registration_cache) {
            register_list.innerHTML = registration_cache[e.target.value];
        } else {
            register_list.innerHTML = "";
        }
        try {
            if (!ndef) {
                ndef = new NDEFReader();
                await ndef.scan();
                out.value = "Scanner actief";

                ndef.addEventListener("readingerror", () => {
                    out.value("Fout opgetreden");
                });

                ndef.addEventListener("reading", async ({message, serialNumber}) => {
                    out.value = "code-> " + serialNumber;
                    const ret = await fetch(Flask.url_for('register.registration'), {method: 'POST', body: JSON.stringify({badge_code: serialNumber.replaceAll(":", ""), location_key: register_type_select.value}),});
                    const resp = await ret.json();
                    let alert = null;
                    let data = null;
                    resp.forEach(i => {
                        if (i.type === "alert-popup") alert = i.data;
                        if (i.type === "update-list-of-registrations") data = i.data.data[0];
                    });
                    if (data) {
                        register_list.innerHTML = `${data.timestamp.substring(11, 19)}, ${data.klascode}, ${data.naam} ${data.voornaam}<br><br>` + register_list.innerHTML;
                        registration_cache[e.target.value] = register_list.innerHTML;
                        localStorage.setItem("registrations", JSON.stringify(registration_cache));
                    } else if (alert) {
                        register_list.innerHTML = `<div style="background:orange;">${alert}</div><br>` + register_list.innerHTML;
                    }

                });
            }
        } catch (error) {
            out.value = "Fout " + error;
        }
    });

    clear_list_button.addEventListener("click", () => {
        bootbox.confirm("Bent u zeker?", result => {
            if (result) {
                if (register_type_select.value in registration_cache) {
                    delete registration_cache[register_type_select.value];
                    localStorage.setItem("registrations", JSON.stringify(registration_cache));
                    register_list.innerHTML = "";
                }
            }
        });
    });
});
