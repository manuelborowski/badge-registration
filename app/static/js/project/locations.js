const location_select = document.createElement("select");
const select_div = document.createElement("div");

export const create_select_locations = locations => {
    select_div.style.display = "none";
    location_select.classList.add("form-select", "form-select-sm");
    location_select.style.marginTop = "8px";
    location_select.style.marginLeft = "8px";
    let select_locations = [["default", "Kies een locatie"], [null, "Geen"]];
    let sort_locations = [];
    for (const location of Object.entries(locations)) {
        sort_locations.push([location[0], location[1].locatie])
    }
    sort_locations.sort((a, b) => a[1] - b[1]);
    select_locations.push(...sort_locations);
    for (const location of select_locations) {
        const option = document.createElement("option");
        option.innerHTML = location[1];
        option.value = location[0];
        location_select.appendChild(option);
    }
    select_div.appendChild(location_select);
    location_select.addEventListener("change", e => handle_location_select());
    const saved_location = localStorage.getItem("badge-location");
    if (saved_location) {
        location_select.value = saved_location;
        handle_location_select(true);
    }
    check_rfidusb_state()
    return select_div
}

//if location has bevestig_met_pin attribute then, at page reload, do not ask for confirmation via pin
const handle_location_select = (at_reload = false) => {
    localStorage.setItem("badge-location", location_select.value)
    if (location_select.value === "default") {
        location_select.style.backgroundColor = "orange";
        rfidusb_set_state(false);
    } else {
        location_select.style.backgroundColor = "lightgreen";
        if (location_select.value === "null") {
            rfidusb_set_state(false)
        } else {
            const location = locations[location_select.value];
            if ("bevestig_met_pin" in location && location.bevestig_met_pin && !at_reload) {
                generate_and_confirm_pin(location_select.value);
            } else {
                rfidusb_set_state(true)
                rfidusb_set_location(location_select.value)
            }
            if ("locatie_reset_om" in location) {
                var reset_at = new Date();
                var [h, m] = location.locatie_reset_om.split(":");
                h = parseInt(h);
                m = parseInt(m);
                reset_at.setHours(h, m, 0);
                const now = new Date();
                if (reset_at > now) {
                    setTimeout(e => {
                        location_select.value = "default";
                        handle_location_select();
                    }, reset_at.getTime() - now.getTime())
                }
            }
        }
    }
}

const generate_and_confirm_pin = (location_key) => {
    const pin = Math.floor(Math.random() * 10000);
    bootbox.prompt({
        title: `Om deze locatie (${locations[location_key].locatie}) te kunnen gebruiken moet je eerst onderstaande pincode ingeven aub.<br>Pin: ${pin}`,
        callback: result => {
            if (result === pin.toString()) {
                rfidusb_set_state(true)
                rfidusb_set_location(location_key);
            } else {
                location_select.value = "default";
                handle_location_select();
            }
        }
    })
}

const rfidusb_set_location = async location => {
    try {
        const ret = await fetch(`${rfidusb_url}/location/${location}`, {method: 'POST'});
        const status = await ret.json();
        var state = status === "ok";
        if (rfidusb_br_url !== "" && state) {
            const encoded_url = encodeURIComponent(encodeURIComponent(rfidusb_br_url));
            const ret = await fetch(`${rfidusb_url}/url/${encoded_url}`, {method: 'POST'});
            const status = await ret.json();
            state = (status === "ok") && state;
        }
        if (rfidusb_br_key !== "" && state) {
            const ret = await fetch(`${rfidusb_url}/api_key/${rfidusb_br_key}`, {method: 'POST'});
            const status = await ret.json();
            state = (status === "ok") && state;
        }

        if (!state) {
            bootbox.alert(`Fout, kan deze locatie niet instellen!`)
        }
    } catch (e) {
        location_select.style.backgroundColor = "orange";
    }
}

const rfidusb_set_state = async state => {
    try {
        const ret = await fetch(`${rfidusb_url}/active/${state ? 1 : 0}`, {method: 'POST'});
        const status = await ret.json();
        if (status !== "ok") {
            bootbox.alert(`Fout, kan de toestand niet aanpassen!`)
        }
    } catch (e) {
        location_select.style.backgroundColor = "orange";
    }
}

var old_rfidusb_state = false;

// if an RFID reader is attached to a USB port (status.port is e.g. COM4), activate the rfidusb server and show the select-location-button
const check_rfidusb_state = async () => {
    try {
        var timeout = 2;
        const ret = await fetch(`${rfidusb_url}/serial_port`);
        const status = await ret.json();
        const rfidusb_state = status.port !== "";
        if (rfidusb_state !== old_rfidusb_state) {
            rfidusb_set_state(rfidusb_state);
            old_rfidusb_state = rfidusb_state;
        }
        select_div.style.display = rfidusb_state ? "block" : "none";
    } catch (e) {
        select_div.style.display = "hidden";
        timeout = 10;
    }
    setTimeout(check_rfidusb_state, timeout * 1000);
}