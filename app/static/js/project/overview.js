import {socketio, Socketio} from "../base/socketio.js";
import {subscribe_get_ids, create_context_menu} from "../base/right_click.js";
import {person_image} from "../../img/base64-person.js";
import {busy_indication_on, busy_indication_off} from "../base/base.js";
import {add_to_popup_body, create_checkbox_element, create_input_element, formio_popup_create, hide_popup, init_popup, show_popup, subscribe_btn_ok} from "../base/popup.js";
import {add_extra_filters, create_filters, enable_filters, disable_filters, subscribe_reset_button} from "../base/filters.js";
import {Rfid} from "./rfidusb.js";
import {check_server_alive, get_my_ip, timed_popup} from "../base/misc.js";

let location_element, date_element, canvas_element, photo_size_element, view_layout_element, sort_on_element,
    sms_specific_element, search_text_element;
let cellphone_specific_element, period_element;
let all_filters_element;

let nbr_registered_element = document.querySelector("#nbr-registered");
let photo_size_factor = 50;
let nbr_registered = 0;
let current_location = null;
let canvas_container = null;


$(document).ready(async function () {
    all_filters_element = document.querySelector(".filters");
    create_filters("Overview", all_filters_element, filters);
    location_element = document.querySelector("#filter-location");
    date_element = document.querySelector("#filter-date");
    canvas_element = document.querySelector("#canvas");
    photo_size_element = document.querySelector("#photo-size-select");
    view_layout_element = document.querySelector("#view-layout-select");
    search_text_element = document.querySelector("#search-text");
    sort_on_element = document.querySelector("#sort-on-select");
    period_element = document.querySelector("#period-select");
    sms_specific_element = document.querySelector("#sms-specific-select")
    cellphone_specific_element = document.querySelector("#cellphone-specific-select")

    // client specific socketio channel
    const private_channel = new Socketio();
    private_channel.start(null, null)
    socketio.subscribe_to_room(await get_my_ip());
    socketio.subscribe_on_receive("alert-popup", (type, data) => timed_popup(type, data, 3000));

    socketio.start(null, null);
    current_location = location_element.value;
    if (!(current_location in locations)) {
        current_location = location_element.options[0].value;
        location_element.options[0].selected = true;
    }
    // each location has it own socketio-room.  This prevents socketio calls to browser that display a different location.
    socketio.subscribe_to_room(current_location);
    // When multiple browsers are displaying the same location, they will be updated simultaneously when e.g. a registration is added
    socketio.subscribe_on_receive("update-list-of-registrations", __socketio_update_list);
    socketio.subscribe_on_receive("update-items-in-list-of-registrations", __socketio_update_items);
    let now = new Date();
    date_element.value = now.toISOString().split("T")[0];
    location_element.addEventListener("change", __location_selection_changed);
    date_element.addEventListener("change", event => __select_date(event));
    search_text_element.addEventListener("keydown", (event) => __do_on_enter_key_pressed(event));
    sort_on_element.addEventListener("change", __request_list_of_registrations_for_current_location);
    view_layout_element.addEventListener("change", __request_list_of_registrations_for_current_location);
    sms_specific_element.addEventListener("change", __request_list_of_registrations_for_current_location);
    period_element.addEventListener("change", __request_list_of_registrations_for_current_location);
    cellphone_specific_element.addEventListener("change", __request_list_of_registrations_for_current_location);
    photo_size_element.addEventListener("change", __resize_photos);
    subscribe_get_ids(__get_ids_of_selected_items_cb);
    subscribe_reset_button(__reset_button_cb);
    Rfid.init();
    Rfid.subscribe_state_change_cb(__rfid_status_changed);
    Rfid.set_managed_state(true);
    __location_selection_changed();
    check_server_alive();
    // In case multiple tabs/browsers to this page are opened, the Rfid-location is set the one that is in focus.
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            Rfid.set_location(current_location)
        }
    });
});

const __location_selection_changed = () => {
    if (current_location !== null) socketio.unsubscribe_from_room(current_location);
    current_location = location_element.value;
    socketio.subscribe_to_room(current_location);
    Rfid.set_location(current_location);
    __request_list_of_registrations_for_current_location();
}

const __rfid_status_changed = status => {
    if (status === Rfid.state.up) {
        location_element.style.background = "lightgreen";
        Rfid.set_location(current_location);
    } else {
        location_element.style.background = "white";
    }
}

// called by the server when the list of registrations is changed, i.e. one or more items (registrations) are added or removed, or a new list is displayed
const __socketio_update_list = (type, data) => {
    if (data.status) {
        const view_tile = view_layout_element.value === "tile";
        if (data.search) {
            disable_filters(Array.from(document.querySelectorAll(".overview-filter")));
            enable_filters(search_text_element);
            search_text_element.focus();
        } else {
            enable_filters(Array.from(document.querySelectorAll(".overview-filter")));
        }
        if (!view_tile && data.headers) {
            let header = document.createElement("tr");
            header.dataset.sort_on = "1";
            data.headers.unshift("<td><input class='select-all' type='checkbox' ''}></td>")
            for (const item of data.headers) {
                const th = document.createElement("th");
                th.innerHTML = item;
                header.appendChild(th);
            }
            canvas_container.prepend(header);
            document.querySelector(".select-all").addEventListener("change", e => {
                [...document.querySelectorAll(".item-select:enabled")].map(i => i.checked = e.target.checked)
            });
        }
        if (data.action === "add") {
            if (!data.date || data.date === date_element.value) {
                for (const item of data.data) {
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
                        if (locations[current_location].type === "cellphone") {
                            const limit = locations[current_location].limiet;
                            if (item.sequence_ctr === limit) {
                                figcaption.style.background = "orangered"
                            } else if (item.sequence_ctr > limit) {
                                figcaption.style.background = "yellow"
                            }
                        }
                    } else {
                        registration_container = document.createElement("tr");
                        registration_container.innerHTML = `
                            <td><input class="item-select" type="checkbox" ""}></td>
                            <td>${item.timestamp}</td>
                            <td data-col="name">${item.naam} ${item.voornaam}</td>
                            <td>${item.klascode}</td>`
                        if (locations[current_location].type === "sms") {
                            registration_container.innerHTML += `
                                <td data-col="sms">${item.sms_sent ? "verstuurd" : "niet verstuurd"}</td> 
                                <td data-col="remark" data-remark-ack="${item.remark_ack}">${item.remark}</td>`;
                            if (item.remark_ack) {
                                registration_container.style.background = "palegreen"
                            }
                        } else if (locations[current_location].type === "cellphone") {
                            const limit = locations[current_location].limiet;
                            registration_container.innerHTML += `
                                <td data-col="message">${(item.sequence_ctr < (limit-1)) ? "NVT" : item.message_sent ? "verstuurd" : "niet verstuurd"}</td> 
                                <td>${item.sequence_ctr}</td>`;
                            if (item.sequence_ctr === limit) {
                                registration_container.style.background = "orangered"
                            } else if (item.sequence_ctr > limit) {
                                registration_container.style.background = "yellow"
                            } else if (item.sequence_ctr < (limit - 1)) {
                                registration_container.firstElementChild.firstChild.disabled = true;
                            }
                        } else if (locations[current_location].type === "toilet") {
                            registration_container.innerHTML += `<td>${item.sequence_ctr}</td>`;
                        } else if (locations[current_location].type === "timeregistration") {
                            registration_container.innerHTML += `<td data-col="time-out">${item.time_out}</td>`;
                        }
                    }
                    registration_container.classList.add("S" + item.leerlingnummer);
                    registration_container.dataset.id = item.id;
                    registration_container.dataset.name = `${item.naam} ${item.voornaam}`;
                    if (sort_on_element.value === "name-firstname") {
                        registration_container.dataset.sort_on = item.naam + item.voornaam;
                    } else if (sort_on_element.value === "klas-name-firstname") {
                        registration_container.dataset.sort_on = item.klascode + item.naam + item.voornaam;
                    } else {
                        registration_container.dataset.sort_on = 100000 - item.id;
                    }
                    for (const container of canvas_container.childNodes) {
                        if (registration_container.dataset.sort_on < container.dataset.sort_on) {
                            container.before(registration_container);
                            break
                        }
                    }
                    __update_nbr_registered();
                    if (locations[current_location].type === "sms") {
                        if (item.auto_remark) __enter_remark([item.id]);
                    }
                }
            }
        } else if (data.action === "delete") {
            data.data.forEach(item => {
                const figure = document.querySelector(`[data-id="${item.id}"]`);
                if (figure) {
                    figure.remove();
                    __update_nbr_registered(true);
                }
            });
        }
        busy_indication_off();
    } else {
        bootbox.alert("Volgende fout is opgetreden:<br>" + data.data);
    }
}

const context_menu_pool = {
    sms: [
        {type: "item", iconscout: "text", label: "Reden", cb: __enter_remark, layout: "list"},
        {type: "item", iconscout: "check", label: "Bevestig reden", cb: to_server_confirm_remark, layout: "list"},
        {type: "item", iconscout: "envelope-send", label: "Stuur sms", cb: to_server_send_message, layout: "list"},
        {type: "divider", layout: "list"}
    ],
    cellphone: [
        {type: "item", iconscout: "envelope-send", label: "Stuur Smartschool bericht", cb: to_server_send_message, layout: "list"},
        {type: "divider", layout: "list"}
    ],
    default: [
        {type: "item", iconscout: "export", label: "Exporteer registraties", cb: () => formio_popup_create(popups["popup-export-registrations"], __export_registrations_cb)},
        {type: "divider", layout: "list"},
        {type: "item", iconscout: "trash-alt", label: "Verwijder registratie", cb: to_server_delete_registration},
        ]
}

const extra_filters_pool = {
    sms: ["sms-specific-select"],
    cellphone: ["cellphone-specific-select"],
    default: []
}

const __request_list_of_registrations_for_current_location = () => {
    busy_indication_on();
    const view_tile = view_layout_element.value === "tile";
    //store the current overview-location-select
    localStorage.setItem("overview-location-select", current_location);
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
        canvas_container.style.margin = "auto";
        const last_row = document.createElement("tr");
        last_row.dataset.sort_on = "zz";
        canvas_container.appendChild(last_row);
    }
    canvas_element.appendChild(canvas_container);
    let filters = {};
    for (const item of Array.from(document.querySelectorAll(".overview-filter"))) {
        filters[item.id] = item.value;
    }
    socketio.send_to_server("request-list-of-registrations", {filters});
    __reset_nbr_registered();

    let context_menu = [];
    if (locations[current_location].type in context_menu_pool) {
        context_menu = context_menu_pool[locations[current_location].type];
        context_menu =  context_menu.concat(context_menu_pool["default"]);
    } else
    {
        context_menu = context_menu_pool["default"];
    }
    context_menu = context_menu.filter(i => !("layout" in i) || i.layout === view_layout_element.value)
    create_context_menu(context_menu);
    const extra_filters = locations[current_location].type in extra_filters_pool ? extra_filters_pool[locations[current_location].type] : extra_filters_pool["default"];
    add_extra_filters(extra_filters);
}

// Called by the server when one or more items are updated, e.g. smartschool message is sent...
const __socketio_update_items = (type, msg) => {
    if (msg.status) {
        for (const item of msg.data) {
            if (document.querySelector(`[data-id="${item.id}"]`) !== null) {
                const row = document.querySelector(`[data-id="${item.id}"]`);
                const view_list = view_layout_element.value === "list";
                if (item.remark !== undefined) {
                    if (view_list) row.querySelector('[data-col="remark"]').innerHTML = item.remark;
                    hide_popup();
                }
                if (item.remark_ack !== undefined) {
                    if (view_list) row.style.background = item.remark_ack ? "palegreen" : "white";
                }
                if (item.sms_sent !== undefined) {
                    if (view_list) row.querySelector('[data-col="sms"]').innerHTML = "verstuurd";
                }
                if (item.ss_message_sent !== undefined) {
                    if (view_list) row.querySelector('[data-col="message"]').innerHTML = "verstuurd";
                }
                if (item.time_out !== undefined) {
                    if (view_list) row.querySelector('[data-col="time-out"]').innerHTML = item.time_out;
                }
            }
        }
    }
}

async function to_server_delete_registration(ids) {
    let message = "";
    if (ids.length === 1) {
        const name = document.querySelector(`[data-id='${ids[0]}']`).dataset.name;
        message = `Wilt u de registratie van ${name} verwijderen?`;
    } else {
        message = `Wilt u de registraties van ${ids.length} personen verwijderen?`;
    }
    bootbox.confirm(message, async result => {
        if (result) {
            const ret = await fetch(Flask.url_for('api.registration_delete'), {
                headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({ids, location: current_location}),
            });
            const status = await ret.json();
            if (!status.status) bootbox.alert(status.data)
            __clear_checkboxes();
        }
    });
}

async function to_server_send_message(ids) {
    let message = "";
    if (ids.length === 1) {
        const name = document.querySelector(`[data-id='${ids[0]}']`).dataset.name;
        message = `Wilt u een bericht sturen betreffende ${name}?`;
    } else {
        message = `Wilt u een bericht sturen betreffende ${ids.length} studenten?`;
    }
    bootbox.confirm(message, async result => {
        if (result) {
            const ret = await fetch(Flask.url_for('api.registration_send_message'), {
                headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({ids, location_key: current_location}),
            });
            const status = await ret.json();
            if (!status.status) bootbox.alert(status.data)
            __clear_checkboxes();
        }
    });
}

const __export_registrations_cb = (action, opaque, data=null) => {
    if (action === 'submit') {
        window.open(`/overview/export/${current_location}/${data.startdate}/${data.enddate}`, '_blank');
    }
}

async function to_server_confirm_remark(ids) {
    const fields = {remark_ack: true};
    const ret = await fetch(Flask.url_for('api.registration_update'), {
        headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({ids, location_key: current_location, fields}),
    });
    const status = await ret.json();
    if (!status.status) bootbox.alert(status.data);
    __clear_checkboxes();
}

async function __enter_remark(ids) {
    const remark_ok_cb = async opaque => {
        const remark = document.querySelector("#remark").value;
        const remark_ack = document.querySelector("#remark_ack").checked;
        if (remark !== null) {
            const fields = {remark, remark_ack}
            const ret = await fetch(Flask.url_for('api.registration_update'), {
                headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({ids, location_key: current_location, fields}),
            });
            const status = await ret.json();
            if (!status.status) bootbox.alert(status.data);
            __clear_checkboxes();
        }
    }
    let text = document.querySelector(`[data-id='${ids[0]}']`).querySelector("[data-col='remark']").innerHTML
    let ack = document.querySelector(`[data-id='${ids[0]}']`).querySelector("[data-col='remark']").dataset.remarkAck;
    text = text === "" ? "Bus " : text;
    ack = ack === "true";
    const name = document.querySelector(`[data-id='${ids[0]}']`).querySelector("[data-col='name']").innerHTML
    const remark_input = create_input_element("Opmerking", "remark", "remark", text, {style: "width: 90%"});
    init_popup({title: name, save_button: false, ok_button: true, width: "75%", default_button: "ok", default_input_element: remark_input});
    add_to_popup_body(remark_input);
    const remark_ack = create_checkbox_element("Bevestigd?", "remark_ack", "remark_ack", ack);
    add_to_popup_body(remark_ack);
    subscribe_btn_ok(remark_ok_cb, null);
    show_popup({focus: remark_input.querySelector("input")});
}

const __get_ids_of_selected_items_cb = mouse_event => {
    let ids = [...document.querySelectorAll(".item-select:checked")].map(e => e.parentElement.parentElement.dataset.id); // if checkboxes are checked
    if (ids.length === 0) ids = [mouse_event.target.parentElement.dataset.id]; // if not, select the current row
    return ids;
}

const __clear_checkboxes = ids => {
    [...document.querySelectorAll(".item-select:checked")].map(e => e.checked = false);
    document.querySelector(".select-all").checked = false;
}

const __resize_photos = () => {
    photo_size_factor = photo_size_element.value;
    __request_list_of_registrations_for_current_location();
}

const __update_nbr_registered = (delete_registration = false) => {
    if (delete_registration) nbr_registered--
    else nbr_registered++;
    if (nbr_registered < 0) nbr_registered = 0;
    nbr_registered_element.value = nbr_registered;
}

const __reset_nbr_registered = () => {
    nbr_registered = 0;
    nbr_registered_element.value = nbr_registered;
}

const __do_on_enter_key_pressed = (event) => {
    if (event.key === "Enter") {
        __request_list_of_registrations_for_current_location();
        search_text_element.value = "";
    }
}

const __select_date = (event) => {
    sms_specific_element.value = "on-date";
    __request_list_of_registrations_for_current_location();
}

const __reset_button_cb = filters => {
    for (const filter of filters) {
        if (filter.name === "filter-location") {
            location_element.value = filter.value;
            __request_list_of_registrations_for_current_location();
        }
    }
}

