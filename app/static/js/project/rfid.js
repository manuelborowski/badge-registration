import { get_data_of_row, update_cell } from "../datatables/datatables.js"
import { badge_raw2hex} from "../base/decode_rfid.js";


async function rfid_to_server(id, rfid, update_endpoint) {
    const ret = await fetch(Flask.url_for(update_endpoint), {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({id, rfid}),});
    const status = await ret.json();
    if (status.status) {
        update_cell(id, 'rfid', rfid);
    } else {
        bootbox.alert(`Kan de RFID code niet aanpassen: ${status.data}`)
    }
}

export async function check_rfid(ids, update_endpoint) {
    let person = get_data_of_row(ids[0]);
    bootbox.prompt({
        title: `Scan de badge van ${person.voornaam} ${person.naam} <br> Of laat leeg om te wissen`,
        callback: result => {
            if (result === '') {
                rfid_to_server(person.id, '', update_endpoint)
            } else if (result) {
                let res = badge_raw2hex(result);
                if (res.valid) {
                    bootbox.dialog({
                        title: 'Nieuwe RFID code?',
                        message: `De gescande code is ${res.code}<br> De huidige code is ${person.rfid}`,
                        // callback: result => {console.log(result)},
                        buttons: {
                            ok: {
                                label: 'Gebruik nieuwe code',
                                className: 'btn-success',
                                callback: () => { rfid_to_server(person.id, res.code, update_endpoint) }
                            },
                            cancel: {
                                label: 'Annuleren',
                                className: 'btn-warning',
                                callback: function () {

                                }
                            },
                        }
                    })
                } else {
                   bootbox.alert("Geen geldige RFID code");
                }
            }
        }
    })
}

