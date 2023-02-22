import {socketio} from "../base/socketio.js";

let location_element = document.querySelector("#filter-location");
let canvas_element = document.querySelector("#canvas");

$(document).ready(function () {
    socketio.start(null, null);
    socketio.subscribe_on_receive("update-actual-status", socketio_update_status);
    location_element.addEventListener("change", event_location_changed);
    event_location_changed();
});


const socketio_update_status = (type, data) => {
    if (data.status) {
        if (data.message.action === "add") {
            data.message.data.forEach(item => {
                let figure = document.createElement("figure");
                figure.id = item.naam;
                let src = "data:image/jpeg;base64," + item.photo;
                let image = document.createElement('img');
                image.src = src;
                image.width = "200";
                let figcaption = document.createElement("figcaption");
                figcaption.innerHTML = item.naam;
                figcaption.style.fontSize = "1.5rem";
                figcaption.style.fontWeight = "bold";
                figure.appendChild(image);
                figure.appendChild(figcaption);
                canvas_element.appendChild(figure);
            });
        }
    } else {
        bootbox.alert("Warning, following error appeared:<br>" + data.message);
    }
}

const event_location_changed = () => {
    socketio.send_to_server("get-all-actual-registrations", {location: location_element.value});
}



