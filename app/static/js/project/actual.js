import {socketio} from "../base/socketio.js";

let location_element = document.querySelector("#filter-location");
let canvas_element = document.querySelector("#canvas");
let photo_size_element = document.querySelector("#photo-size-select");
let photo_size_factor = 100;

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
                figure.classList.add(item.username);
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
            });
        } else if (data.action === "delete") {
            data.data.forEach(item => {
                let figures = document.querySelectorAll("." + item.username);
                figures.forEach(item => {item.remove()});
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
}


export const remove_all_photos = () => {
    socketio.send_to_server("clear-all-registrations", {location: location_element.value});
    get_actual_registrations();
}

const resize_photos = () => {
    photo_size_factor = photo_size_element.value;
    get_actual_registrations();
}