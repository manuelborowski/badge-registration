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
