import {socketio} from "../base/socketio.js";
import {subscribe_get_ids, create_menu} from "../base/right_click.js";
import {person_image} from "../../img/base64-person.js";
import {busy_indication_on, busy_indication_off} from "../base/base.js";
import {add_to_popup_body, create_checkbox_element, create_input_element, init_popup, show_popup, subscribe_btn_ok} from "../base/popup.js";

let location_element = document.querySelector("#filter-location");
let date_element = document.querySelector("#filter-date");
let canvas_element = document.querySelector("#canvas");
let photo_size_element = document.querySelector("#photo-size-select");
let view_layout_element = document.querySelector("#view-layout-select");
let sort_on_element = document.querySelector("#sort-on-select");
let title_element = document.querySelector(".title-element");
let nbr_registered_element = document.querySelector("#nbr-registered");
let photo_size_factor = 50;
let nbr_registered = 0;
let current_room = "";
let canvas_container = null;


const right_click_menu = {
    remark: {iconscout: "text", label: "Reden", cb: enter_remark},
    sms: {iconscout: "envelope-send", label: "Stuur sms", cb: to_server_send_sms},
    delete: {iconscout: "trash-alt", label: "Verwijder registratie", cb: to_server_delete_registration},
    ack: {iconscout: "check", label: "Bevestig reden", cb: to_server_confirm_remark},

}

$(document).ready(function () {
    socketio.start(null, null);
    current_room = location_element.value;
    socketio.subscribe_to_room(current_room);
    socketio.subscribe_on_receive("update-current-status", socketio_update_status);
    socketio.subscribe_on_receive("update-registration", socketio_update_registration);
    let now = new Date();
    date_element.value = now.toISOString().split("T")[0];
    location_element.addEventListener("change", get_current_registrations);
    date_element.addEventListener("change", get_current_registrations);
    sort_on_element.addEventListener("change", get_current_registrations);
    view_layout_element.addEventListener("change", get_current_registrations);
    photo_size_element.addEventListener("change", resize_photos);
    subscribe_get_ids(get_ids_of_selected_items);

    //if a filter is changed, then the filter is applied by simulating a click on the filter button
    $(".overview-filter").change(function () {
        store_filter_settings();
    });

    //Store locally in the client-browser
    function store_filter_settings() {
        var filter_settings = [];
        if (filters.length > 0) {
            filters.forEach(f => {
                if (f.store === undefined || f.store === true) {
                    if (f.type === 'select') {
                        filter_settings.push({
                            name: f.name,
                            type: f.type,
                            value: document.querySelector(`#${f.name} option:checked`).value
                        });
                    } else if (f.type === 'checkbox') {
                        let boxes = [];
                        f.boxes.forEach(([k, l]) => {
                            boxes.push({id: k, checked: document.querySelector(`#${k}`).checked})
                        });
                        filter_settings.push({
                            name: f.name,
                            type: f.type,
                            value: boxes
                        })
                    } else if (f.type === 'text' || f.type === 'date') {
                        filter_settings.push({
                            name: f.name,
                            type: f.type,
                            value: document.querySelector(`#${f.name}`).value
                        })
                    }
                }
            });
            localStorage.setItem(`Filter-overview`, JSON.stringify(filter_settings));
        }
    }

    function load_filter_settings() {
        if (filters.length === 0) return true;
        var filter_settings = JSON.parse(localStorage.getItem(`Filter-overview`));
        if (!filter_settings) {
            filter_settings = [];
            return false
        }
        filter_settings.forEach(f => {
            if (f.type === 'select' || f.type === 'text' || f.type === 'date') {
                document.querySelector(`#${f.name}`).value = f.value;
            }
        })
        return true;
    }

    if (!load_filter_settings()) store_filter_settings(); //filters are applied when the page is loaded for the first time

    get_current_registrations();
});

export function clear_filter_setting() {
    localStorage.clear(`Filter-overview`);
    location.reload();
}

const socketio_update_status = (type, data) => {
    if (data.status) {
        const view_tile = view_layout_element.value === "tile";
        if (data.action === "add") {
            if (data.selected_day === date_element.value) {
                data.data.forEach(item => {
                    let registration_container = null;
                    if (view_tile) {
                        registration_container = document.createElement("figure");
                        registration_container.style.display = "inline-block";
                        registration_container.style.marginRight = "10px";
                        registration_container.style.zIndex = "1";
                        let src = "data:image/jpeg;base64," + (item.photo !== "" ? item.photo : person_image);
                        let image = document.createElement('img');
                        image.src = src;
                        image.width = (2 * photo_size_factor).toString();
                        let figcaption = document.createElement("figcaption");
                        figcaption.innerHTML = "(" + item.timestamp.split(" ")[1] + ") " + item.klascode + "<br>" + item.naam + " " + item.voornaam;
                        figcaption.style.fontSize = (1.5 * photo_size_factor / 100).toString() + "rem";
                        figcaption.style.fontWeight = "bold";
                        figcaption.style.textAlign = "center";
                        registration_container.appendChild(image);
                        registration_container.appendChild(figcaption);
                    } else {
                        registration_container = document.createElement("tr");
                        registration_container.innerHTML = `
                            <td><input data-col="sms" type="checkbox" ${item.sms_sent ? "checked" : ""}></td> 
                            <td>${item.timestamp.split(" ")[1]}</td> 
                            <td>${item.naam} ${item.voornaam}</td> 
                            <td>${item.klascode}</td> 
                            <td data-col="remark">${item.remark}</td>`;
                        if (item.remark_ack) {
                            registration_container.style.background = "palegreen"
                        }
                    }
                    registration_container.classList.add("S" + item.leerlingnummer, "mtooltip");
                    registration_container.dataset.id = item.id;
                    if (sort_on_element.value === "name-firstname") {
                        registration_container.dataset.sort_on = item.naam + item.voornaam;
                    } else if (sort_on_element.value === "klas-name-firstname") {
                        registration_container.dataset.sort_on = item.klascode + item.naam + item.voornaam;
                    } else {
                        registration_container.dataset.sort_on = 1000 - item.id;
                    }
                    const tooltip_span = document.createElement("span");
                    tooltip_span.classList.add("tooltiptext");
                    registration_container.appendChild(tooltip_span)
                    for (const container of canvas_container.childNodes) {
                        if (registration_container.dataset.sort_on < container.dataset.sort_on) {
                            container.before(registration_container);
                            break
                        }
                    }
                    update_tooltip_items(item.id, {name: `${item.naam} ${item.voornaam}`, remark: item.remark, remark_ack: item.remark_ack, sms_sent: item.sms_sent})
                    update_nbr_registered();
                });
            }
        } else if (data.action === "delete") {
            data.data.forEach(item => {
                const figure = document.querySelector(`[data-id="${item.id}"]`);
                if (figure) {
                    figure.remove();
                    update_nbr_registered(true);
                }
            });
        }
        busy_indication_off();
    } else {
        bootbox.alert("Volgende fout is opgetreden:<br>" + data.data);
    }
}

const get_current_registrations = () => {
    busy_indication_on();
    const view_tile = view_layout_element.value === "tile";
    socketio.unsubscribe_from_room(current_room);
    current_room = location_element.value;
    socketio.subscribe_to_room(current_room);
    let location_label = location_element.options[location_element.selectedIndex].innerHTML;
    canvas_element.innerHTML = "";
    // Add dummy element to indicate end of list
    if (view_tile) {
        canvas_container = document.createElement("div");
        const sentinel = document.createElement("div");
        sentinel.dataset.sort_on = "zz";
        canvas_container.appendChild(sentinel);
    } else {
        canvas_container = document.createElement("table")
        const last_row = document.createElement("tr");
        last_row.dataset.sort_on = "zz";
        canvas_container.appendChild(last_row);
    }
    canvas_element.appendChild(canvas_container);
    socketio.send_to_server("get-current-registrations", {location: location_element.value, date: date_element.value});
    reset_nbr_registered();
    create_menu(current_room, right_click_menu);
}

export const remove_all_photos = () => {
    socketio.send_to_server("clear-all-registrations", {location: location_element.value});
    get_current_registrations();
}

const resize_photos = () => {
    photo_size_factor = photo_size_element.value;
    get_current_registrations();
}

const update_nbr_registered = (delete_registration = false) => {
    if (delete_registration) nbr_registered--
    else nbr_registered++;
    if (nbr_registered < 0) nbr_registered = 0;
    nbr_registered_element.value = nbr_registered;
}

const reset_nbr_registered = () => {
    nbr_registered = 0;
    nbr_registered_element.value = nbr_registered;
}

async function to_server_delete_registration(ids) {
    const name = get_tooltip(ids[0], "name");
    bootbox.confirm(`Wilt u de registratie van ${name} verwijderen?`, async result => {
        if (result) {
            const ret = await fetch(Flask.url_for('api.registration_delete'), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({ids, location: current_room}),});
            const status = await ret.json();
            if (status.status) {
                // get_current_registrations()
            } else {
                bootbox.alert(status.data)
            }
        }
    });
}

// Check if data.data.id is valid, i.e. is present.  If not, it is because another browser did an update on a different date.
const socketio_update_registration = (type, data) => {
    if (data.status && document.querySelector(`[data-id="${data.data.id}"]`) !== null ) {
        const row = document.querySelector(`[data-id="${data.data.id}"]`);
        if (data.data.fields.remark) {
            update_tooltip_items(data.data.id, {remark: data.data.fields.remark});
            row.querySelector('[data-col="remark"]').innerHTML = data.data.fields.remark;
        }
        if (data.data.fields.remark_ack !== undefined) {
            update_tooltip(data.data.id, {remark_ack: data.data.fields.remark_ack});
            row.style.background = data.data.fields.remark_ack ? "palegreen" : "white";
        }
        if (data.data.fields.sms_sent !== undefined) {
            update_tooltip(data.data.id, {sms_sent: data.data.fields.sms_sent});
            row.querySelector('[data-col="sms"]').checked = data.data.fields.sms_sent;
        }
    }
}

async function to_server_send_sms(ids) {
    const name = get_tooltip(ids[0], "name");
    bootbox.confirm(`Wilt u een sms sturen naar de ouders van ${name}?`, async result => {
        if (result) {
            const ret = await fetch(Flask.url_for('api.registration_send_sms'), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({id: ids[0], location_key: current_room}),});
            const status = await ret.json();
            if (!status.status) {
                bootbox.alert(status.data)
            }
        }
    });
}

async function to_server_confirm_remark(ids) {
    const fields = {remark_ack: true};
    const ret = await fetch(Flask.url_for('api.registration_update'), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({id: ids[0], location_key: current_room, fields}),});
    const status = await ret.json();
    if (!status.status) {
        bootbox.alert(status.data);
    }
}

async function enter_remark(ids) {
    const remark_ok_cb = async opaque => {
        const remark = document.querySelector("#remark").value;
        const remark_ack = document.querySelector("#remark_ack").checked;
        if (remark !== null) {
            const fields = {remark, remark_ack}
            const ret = await fetch(Flask.url_for('api.registration_update'), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({id: ids[0], location_key: current_room, fields}),});
            const status = await ret.json();
            if (!status.status) {
                bootbox.alert(status.data);
            }
        }
    }

    var text = get_tooltip(ids[0], "remark");
    text = text === "" ? "Bus " : text;
    var ack = get_tooltip(ids[0], "remark_ack");
    ack = ack === "true";
    const name = get_tooltip(ids[0], "name");
    init_popup({title: name, save_button: false, ok_button: true, width: "75%"});
    const remark_input = create_input_element("Opmerking", "remark", "remark", text, {style: "width: 90%"});
    add_to_popup_body(remark_input);
    const remark_ack = create_checkbox_element("Bevestigd?", "remark_ack", "remark_ack", ack);
    add_to_popup_body(remark_ack);
    subscribe_btn_ok(remark_ok_cb, null);
    show_popup();
}

const tooltip_items = [{item: "name", label: "naam"}, {item: "remark", label: "opm"}, {item: "remark_ack", label: "Bevestigd?", type: "bool"}, {item: "sms_sent", label: "sms verzonden?", type: "bool"}];

const update_tooltip_items = (id, items) => {
    const tooltip = document.querySelector(`[data-id="${id}"] .tooltiptext`);
    for(const key in items) {
        tooltip.dataset[key] = items[key];
    }
    let html = "";
    for (const item of tooltip_items) {
        if (item.type === "bool") {
            html += `${item.label}: ${tooltip.dataset[item.item] === "true" ? "JA" : "NEE"}<br>`;
        } else {
            html += `${item.label}: ${tooltip.dataset[item.item]}<br>`;
        }
    }
    tooltip.innerHTML = html;
    tooltip.classList.add("tooltiptext");
}

const get_tooltip = (id, item) => {
    const tooltip = document.querySelector(`[data-id="${id}"] .tooltiptext`);
    return tooltip.dataset[item];
}

const get_ids_of_selected_items = mouse_event => {
    const ids = [mouse_event.target.parentElement.dataset.id];
    return ids;
}
