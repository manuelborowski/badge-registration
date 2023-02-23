import {socketio} from "../base/socketio.js";

let location_element = document.querySelector("#filter-location");
let canvas_element = document.querySelector("#canvas");

$(document).ready(function () {
    socketio.start(null, null);
    socketio.subscribe_on_receive("update-actual-status", socketio_update_status);
    location_element.addEventListener("change", get_actual_registrations);
    get_actual_registrations();
});


const socketio_update_status = (type, data) => {
    if (data.status) {
        if (data.action === "add") {
            data.data.forEach(item => {
                let figures = document.querySelectorAll(".fig-group");
                let figure = document.createElement("figure");
                figure.id = (item.naam + item.voornaam).replaceAll(" ", "-");
                figure.classList.add("fig-group");
                figure.style.display = "inline-block";
                figure.style.marginRight = "10px";
                let src = "data:image/jpeg;base64," + item.photo;
                let image = document.createElement('img');
                image.src = src;
                image.width = "200";
                let figcaption = document.createElement("figcaption");
                figcaption.innerHTML = item.naam + "<br>" + item.voornaam;
                figcaption.style.fontSize = "1.5rem";
                figcaption.style.fontWeight = "bold";
                figcaption.style.textAlign = "center";
                figure.appendChild(image);
                figure.appendChild(figcaption);
                for (let i=0; i < figures.length; i++ ) {
                    if (figure.id < figures[i].id) {
                        figures[i].before(figure);
                        break;
                    }
                }
            });
        } else if (data.action === "delete") {
            data.data.forEach(item => {
                let figure = document.querySelector("#" + (item.naam + item.voornaam).replaceAll(" ", "-"));
                if (figure !== null) {
                    figure.remove();
                }
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
    figure.id = "ZZZZZZZZZ";
    figure.classList.add("fig-group");
    canvas_element.appendChild(figure);
    socketio.send_to_server("get-all-actual-registrations", {location: location_element.value});
}


export const remove_all_photos = () => {
    socketio.send_to_server("clear-all-registrations", {location: location_element.value});
    get_actual_registrations();
}

