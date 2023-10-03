import {socketio} from "../base/socketio.js";
import {subscribe_get_ids, subscribe_right_click} from "../base/right_click.js";
import { person_image } from "../../img/base64-person.js";
import { busy_indication_on, busy_indication_off } from "../base/base.js";

let location_element = document.querySelector("#filter-location");
let date_element = document.querySelector("#filter-date");
let canvas_element = document.querySelector("#canvas");
let photo_size_element = document.querySelector("#photo-size-select");
let sort_on_element = document.querySelector("#sort-on-select");
let title_element = document.querySelector(".title-element");
let nbr_registered_element = document.querySelector("#nbr-registered");
let photo_size_factor = 50;
let nbr_registered = 0;
let current_room = "";

$(document).ready(function () {
    socketio.start(null, null);
    current_room = location_element.value;
    socketio.subscribe_to_room(current_room);
    socketio.subscribe_on_receive("update-current-status", socketio_update_status);
    let now = new Date();
    date_element.value = now.toISOString().split("T")[0];
    location_element.addEventListener("change", get_current_registrations);
    date_element.addEventListener("change", get_current_registrations);
    sort_on_element.addEventListener("change", get_current_registrations);
    photo_size_element.addEventListener("change", resize_photos);
    subscribe_get_ids(get_ids_of_selected_items);

    get_current_registrations();
});


const socketio_update_status = (type, data) => {
    if (data.status) {
        if (data.selected_day === date_element.value) {
            if (data.action === "add") {
                data.data.forEach(item => {
                    let figures = document.querySelectorAll(".fig-group");
                    let figure = document.createElement("figure");
                    figure.classList.add("S" + item.leerlingnummer);
                    if (sort_on_element.value === "name-firstname") {
                        figure.dataset.sort_on = item.naam + item.voornaam;
                    } else if (sort_on_element.value === "klas-name-firstname") {
                        figure.dataset.sort_on = item.klascode + item.naam + item.voornaam;
                    } else {
                        figure.dataset.sort_on = 1000 - item.id;
                    }
                    figure.classList.add("fig-group");
                    figure.style.display = "inline-block";
                    figure.style.marginRight = "10px";
                    figure.dataset.id = item.id;
                    let src = "data:image/jpeg;base64," + (item.photo !== "" ? item.photo : person_image);
                    let image = document.createElement('img');
                    image.src = src;
                    let image_width = 2 * photo_size_factor;
                    image.width = (2 * photo_size_factor).toString();
                    let figcaption = document.createElement("figcaption");
                    figcaption.innerHTML = "(" + item.timestamp.split(" ")[1] + ") " + item.klascode + "<br>" + item.naam + " " + item.voornaam;
                    figcaption.style.fontSize = (1.5 * photo_size_factor / 100).toString() + "rem";
                    figcaption.style.fontWeight = "bold";
                    figcaption.style.textAlign = "center";
                    figure.appendChild(image);
                    figure.appendChild(figcaption);
                    for (let i = 0; i < figures.length; i++) {
                        if (figure.dataset.sort_on < figures[i].dataset.sort_on) {
                            figures[i].before(figure);
                            break;
                        }
                    }
                    update_nbr_registered();
                });
            } else if (data.action === "delete") {
                data.data.forEach(item => {
                    let figure = document.querySelector(".S" + item.leerlingnummer);
                    figure.remove();
                    update_nbr_registered(true);
                });
            }
        }
        busy_indication_off();
    } else {
        bootbox.alert("Warning, following error appeared:<br>" + data.data);
    }
}

const get_current_registrations = () => {
    busy_indication_on();
    socketio.unsubscribe_from_room(current_room);
    current_room = location_element.value;
    socketio.subscribe_to_room(current_room);
    let location_label = location_element.options[location_element.selectedIndex].innerHTML;
    // let title = title_element.innerHTML.split(": ")[0];
    // title_element.innerHTML = title;
    canvas_element.innerHTML = "";
    // Add dummy figure to indicate end of list
    let figure = document.createElement("div");
    figure.dataset.sort_on = "zz";
    figure.classList.add("fig-group");
    canvas_element.appendChild(figure);
    socketio.send_to_server("get-current-registrations", {location: location_element.value, date: date_element.value});
    reset_nbr_registered();
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

const delete_registration = async (item, ids) => {
    bootbox.confirm("Wilt u deze registratie verwijderen?", async result => {
        if (result) {
            const ret = await fetch(Flask.url_for('api.registration_delete'), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify(ids),});
            const status = await ret.json();
            if (status.status) {
                // bootbox.alert(`Registratie is verwijderd.`)
                get_current_registrations()
            } else {
                bootbox.alert(status.data)
            }
        }
    });
}


const get_ids_of_selected_items = mouse_event => {
    const ids = [mouse_event.target.parentElement.dataset.id];
    return ids;
}

subscribe_right_click('delete', (item, ids) => delete_registration(item, ids));
