export function flash_messages(list) {
    for (var i = 0; i < list.length; i++) {
        var message = list[i];
        bootbox.alert(message);
    }
}

export function busy_indication_on() {
    document.getElementsByClassName("busy-indicator")[0].style.display = "block";
}

export function busy_indication_off() {
    document.getElementsByClassName("busy-indicator")[0].style.display = "none";
}

export const start_sync = async () => {
    var test = [
        ["2023-10-15T15:51:23", "37DC30EE", "test"],
        ["2023-10-15T15:51:25", "1234", "verdiep"],
        ["2023-08-25T12:00:45", "97281C08", "f005drank"],
        ["2023-08-25T12:03:04", "771A2EEE", "f005drank"],
    ]
    busy_indication_on();
    var message = "Start met synchroniseren van leerlingen..."
    bootbox.dialog({
       message: `<span id='sync-message'>${message}</span>`,
       title: "Synchroniseer leerlingen en registraties",
       buttons: {main: {label: "OK", className: "btn-primary",}
      }
    });
    const ret = await fetch(Flask.url_for('api.sync_students_start'), {headers: {'x-api-key': api_key,}, method: 'POST'});
    const status = await ret.json();
    if (status.status) {
        message += `\n-> Nieuwe studenten: ${status.data.nbr_new}, Aangepaste studenten: ${status.data.nbr_updated}, Verwijderde studenten: ${status.data.nbr_deleted}`
        message += `\n\nStart met synchroniseren van registraties...`
        document.querySelector("#sync-message").innerText = message;
    }
    const ret2 = await fetch(Flask.url_for('api.sync_registrations_start'), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify(test)});
    const status2 = await ret2.json();
    if (status2.status) {
        message += `\n->Nieuwe registraties: ${status2.data.nbr_new}, Dubbele registraties: ${status2.data.nbr_doubles}`
        message += `\n\nSynchroniseren is gedaan`
        document.querySelector("#sync-message").innerText = message;
    }
    busy_indication_off();
}

var menu = [
    ["overview.show_nietverplicht", "Niet-verplicht", 1],
    ["overview.show_verkoop", "Verkoop", 1],
    ["student.show", "Studenten", 1],
    ["user.show", "Gebruikers", 5],
    ["settings.show", "Instellingen", 5],
]


export const inject_menu = new_menu => {
    menu = new_menu;
}

$(document).ready(() => {
    const navbar_element = document.querySelector("#navbar");
    let dd_ctr = 0;
    for (const item of menu) {
        if (current_user_level >= item[2]) {
            const li = document.createElement("li");
            if (Array.isArray(item[0])) {
                // dropdown menu-item
                li.classList.add("nav-item", "dropdown");
                const a = document.createElement("a");
                li.appendChild(a)
                a.classList.add("nav-link", "dropdown-toggle");
                a.href = "#";
                a.id = `dd${dd_ctr}`
                a.setAttribute("role", "button");
                a.setAttribute("data-toggle", "dropdown");
                a.setAttribute("aria-haspopup", true);
                a.setAttribute("aria-expanded", true);
                a.innerHTML = item[1];
                const div = document.createElement("div");
                li.appendChild(div)
                div.classList.add("dropdown-menu");
                div.setAttribute("aria-labelledby", `dd${dd_ctr}`)
                for (const sitem of item[0]) {
                    if (sitem[0] === "divider") {
                        const divd = document.createElement("div");
                        divd.classList.add("dropdown-divider");
                        div.appendChild(divd)
                    } else {
                        if (current_user_level >= sitem[2]) {
                            const a = document.createElement("a");
                            div.appendChild(a)
                            a.classList.add("dropdown-item");
                            if (typeof sitem[0] === "function") {
                                a.onclick = sitem[0];
                            } else {
                                a.href = Flask.url_for(sitem[0]);
                            }
                            a.innerHTML = sitem[1]
                        }
                    }
                }
                dd_ctr++;

            } else {
                // regular menu-item
                const url_path = Flask.url_for(item[0]);
                li.classList.add("nav-item");
                const a = document.createElement("a");
                a.classList.add("nav-link");
                if (window.location.href.includes(url_path)) {
                    a.classList.add("active");
                }
                a.href = url_path;
                a.innerHTML = item[1];
                li.appendChild(a);
            }
            navbar_element.appendChild(li);
        }
    }

    if (stand_alone) {
        const btn_div = document.createElement("div");
        btn_div.classList.add("nav-buttons");
        const sync_btn = document.createElement("button");
        sync_btn.classList.add("btn", "btn-warning");
        sync_btn.type = "button";
        sync_btn.onclick = start_sync;
        sync_btn.innerHTML = "Sync";
        btn_div.appendChild(sync_btn);
        navbar_element.appendChild(btn_div);
    }
});

