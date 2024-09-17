import {socketio} from "../base/socketio.js";
import {subscribe_get_ids, create_context_menu} from "../base/right_click.js";
import {person_image} from "../../img/base64-person.js";
import {busy_indication_on, busy_indication_off} from "../base/base.js";
import {add_to_popup_body, create_checkbox_element, create_input_element, init_popup, show_popup, subscribe_btn_ok} from "../base/popup.js";
import {add_extra_filters, create_filters, enable_filters, disable_filters, subscribe_reset_button} from "../base/filters.js";

let location_element,date_element, canvas_element, photo_size_element, view_layout_element, sort_on_element, sms_specific_element, search_text_element;
let all_filters_element;

let nbr_registered_element = document.querySelector("#nbr-registered");
let photo_size_factor = 50;
let nbr_registered = 0;
let current_location = "";
let canvas_container = null;


$(document).ready(function () {
    all_filters_element = document.querySelector(".filters");
    create_filters("Overview", all_filters_element, filters);
    location_element = document.querySelector("#filter-location");
    date_element = document.querySelector("#filter-date");
    canvas_element = document.querySelector("#canvas");
    photo_size_element = document.querySelector("#photo-size-select");
    view_layout_element = document.querySelector("#view-layout-select");
    search_text_element = document.querySelector("#search-text");
    sort_on_element = document.querySelector("#sort-on-select");
    sms_specific_element = document.querySelector("#sms-specific-select")

    socketio.start(null, null);
    current_location = location_element.value;
    socketio.subscribe_to_room(current_location);
    socketio.subscribe_on_receive("update-current-status", socketio_update_status);
    socketio.subscribe_on_receive("update-registration", socketio_update_registration);
    let now = new Date();
    date_element.value = now.toISOString().split("T")[0];
    location_element.addEventListener("change", get_current_registrations);
    date_element.addEventListener("change", event => __select_date(event));
    search_text_element.addEventListener("keydown", (event) => __wait_for_enter(event));
    sort_on_element.addEventListener("change", get_current_registrations);
    view_layout_element.addEventListener("change", get_current_registrations);
    sms_specific_element.addEventListener("change", get_current_registrations);
    photo_size_element.addEventListener("change", resize_photos);
    subscribe_get_ids(get_ids_of_selected_items);
    subscribe_reset_button(__reset_button_cb);
    get_current_registrations();
});

const socketio_update_status = (type, data) => {
    if (data.status) {
        const view_tile = view_layout_element.value === "tile";
        if (data.search) {
            disable_filters(Array.from(document.querySelectorAll(".overview-filter")));
            enable_filters(search_text_element);
            search_text_element.focus();
        } else {
            enable_filters(Array.from(document.querySelectorAll(".overview-filter")));
        }
        if (data.action === "add") {
            if ( !data.date || data.date === date_element.value) {
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
                        if (locations[current_location].type === "cellphone") {
                            if (item.limit_reached) {
                                figcaption.style.background = "lightpink"
                            }
                        }
                    } else {
                        registration_container = document.createElement("tr");
                        if (locations[current_location].type === "sms") {
                            registration_container.innerHTML = `
                            <td>SMS: <input data-col="sms" type="checkbox" ${item.sms_sent ? "checked" : ""}></td> 
                            <td>${item.timestamp}</td> 
                            <td>${item.naam} ${item.voornaam}</td> 
                            <td>${item.klascode}</td> 
                            <td data-col="remark">${item.remark}</td>`;
                            if (item.remark_ack) {
                                registration_container.style.background = "palegreen"
                            }
                        } else if (locations[current_location].type === "cellphone") {
                            registration_container.innerHTML = `
                            <td>${item.timestamp}</td> 
                            <td>${item.naam} ${item.voornaam}</td> 
                            <td>${item.klascode}</td>`;
                            if (item.limit_reached) {
                                registration_container.style.background = "lightpink"
                            }
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

const __wait_for_enter = (event) => {
    if (event.key === "Enter") {
        get_current_registrations();
        search_text_element.value = "";
    }
}

const __select_date = (event) => {
    sms_specific_element.value = "on_date";
    get_current_registrations();
}

const __reset_button_cb = filters => {
    for (const filter of filters) {
        if (filter.name === "filter-location") {
            location_element.value = filter.value;
            get_current_registrations();
        }
    }
}

const context_menu_pool = {
    sms: [
    {type: "item", iconscout: "text", label: "Reden", cb: enter_remark},
    {type: "item", iconscout: "check", label: "Bevestig reden", cb: to_server_confirm_remark},
    {type: "item", iconscout: "envelope-send", label: "Stuur sms", cb: to_server_send_sms},
    {type: "divider"},
    {type: "item", iconscout: "trash-alt", label: "Verwijder registratie", cb: to_server_delete_registration}],
    default: [{type: "item", iconscout: "trash-alt", label: "Verwijder registratie", cb: to_server_delete_registration}]
}

const extra_filters_pool = {
    sms: ["search-text", "view-layout-select", "sms-specific-select"],
    cellphone: ["search-text", "view-layout-select"],
    default: []
}

const get_current_registrations = () => {
    busy_indication_on();
    const view_tile = view_layout_element.value === "tile";
    socketio.unsubscribe_from_room(current_location);
    current_location = location_element.value;
    socketio.subscribe_to_room(current_location);
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
    const filter = {date: date_element.value, sms_specific: sms_specific_element.value, search_text: search_text_element.value}
    socketio.send_to_server("get-current-registrations", {location: current_location, filter, include_foto: view_tile});
    reset_nbr_registered();

    const context_menu = locations[current_location].type in context_menu_pool ? context_menu_pool[locations[current_location].type] : context_menu_pool["default"];
    create_context_menu(context_menu);
    const extra_filters = locations[current_location].type in extra_filters_pool ? extra_filters_pool[locations[current_location].type] : extra_filters_pool["default"];
    add_extra_filters(extra_filters);
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
            const ret = await fetch(Flask.url_for('api.registration_delete'), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({ids, location: current_location}),});
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
        const view_list = view_layout_element.value === "list";
        if (data.data.fields.remark) {
            update_tooltip_items(data.data.id, {remark: data.data.fields.remark});
            if (view_list) row.querySelector('[data-col="remark"]').innerHTML = data.data.fields.remark;
        }
        if (data.data.fields.remark_ack !== undefined) {
            update_tooltip_items(data.data.id, {remark_ack: data.data.fields.remark_ack});
            if (view_list) row.style.background = data.data.fields.remark_ack ? "palegreen" : "white";
        }
        if (data.data.fields.sms_sent !== undefined) {
            update_tooltip_items(data.data.id, {sms_sent: data.data.fields.sms_sent});
            if (view_list) row.querySelector('[data-col="sms"]').checked = data.data.fields.sms_sent;
        }
    }
}

async function to_server_send_sms(ids) {
    const name = get_tooltip(ids[0], "name");
    bootbox.confirm(`Wilt u een sms sturen naar de ouders van ${name}?`, async result => {
        if (result) {
            const ret = await fetch(Flask.url_for('api.registration_send_sms'), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({id: ids[0], location_key: current_location}),});
            const status = await ret.json();
            if (!status.status) {
                bootbox.alert(status.data)
            }
        }
    });
}

async function to_server_confirm_remark(ids) {
    const fields = {remark_ack: true};
    const ret = await fetch(Flask.url_for('api.registration_update'), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({id: ids[0], location_key: current_location, fields}),});
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
            const ret = await fetch(Flask.url_for('api.registration_update'), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({id: ids[0], location_key: current_location, fields}),});
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
