import {socketio} from "../base/socketio.js";

let location_element = document.querySelector("#filter-location");
let canvas_element = document.querySelector("#canvas");
let photo_size_element = document.querySelector("#photo-size-select");
let nbr_registered_element = document.querySelector("#nbr-registered");
let photo_size_factor = 100;
let nbr_registered = 0;

$(document).ready(function () {
    socketio.start(null, null);
    socketio.subscribe_on_receive("update-actual-status", socketio_update_status);
    location_element.addEventListener("change", get_actual_registrations);
    photo_size_element.addEventListener("change", resize_photos);
    get_actual_registrations();
});


const socketio_update_status = (type, data) => {
    if (data.status) {
        if (data.action === "add") {
            data.data.forEach(item => {
                let figures = document.querySelectorAll(".fig-group");
                let figure = document.createElement("figure");
                figure.classList.add(item.leerlingnummer);
                figure.dataset.sort_on = item.klascode + item.naam + item.voornaam;
                figure.classList.add("fig-group");
                figure.style.display = "inline-block";
                figure.style.marginRight = "10px";
                let src = "data:image/jpeg;base64," + item.photo;
                let image = document.createElement('img');
                image.src = src;
                let image_width = 2 * photo_size_factor;
                image.width = (2 * photo_size_factor).toString();
                let figcaption = document.createElement("figcaption");
                figcaption.innerHTML = item.klascode + "<br>" + item.naam + " " + item.voornaam;
                figcaption.style.fontSize = (1.5 * photo_size_factor / 100).toString() + "rem";
                figcaption.style.fontWeight = "bold";
                figcaption.style.textAlign = "center";
                figure.appendChild(image);
                figure.appendChild(figcaption);
                for (let i=0; i < figures.length; i++ ) {
                    if (figure.dataset.sort_on < figures[i].dataset.sort_on) {
                        figures[i].before(figure);
                        break;
                    }
                }
                update_nbr_registered();
            });
        } else if (data.action === "delete") {
            data.data.forEach(item => {
                let figures = document.querySelectorAll("." + item.leerlingnummer);
                figures.forEach(item => {item.remove()});
                update_nbr_registered(true);
            });
        }
    } else {
        bootbox.alert("Warning, following error appeared:<br>" + data.data);
    }
}

const get_actual_registrations = () => {
    canvas_element.innerHTML = "";
    // Add dummy figure to indicate end of list
    let figure = document.createElement("div");
    figure.dataset.sort_on = "zz";
    figure.classList.add("fig-group");
    canvas_element.appendChild(figure);
    socketio.send_to_server("get-all-actual-registrations", {location: location_element.value});
    reset_nbr_registered();
}


export const remove_all_photos = () => {
    socketio.send_to_server("clear-all-registrations", {location: location_element.value});
    get_actual_registrations();
}

const resize_photos = () => {
    photo_size_factor = photo_size_element.value;
    get_actual_registrations();
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