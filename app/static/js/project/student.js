import {subscribe_get_ids, create_context_menu} from "../base/right_click.js";
import { ctx, get_data_of_row } from "../datatables/datatables.js"

let menu_item2label = {};

const __registration_add = async (item, ids) => {
   let person = get_data_of_row(ids[0]);
    bootbox.confirm(`${menu_item2label[item]}<br>Voor: ${person.naam} ${person.voornaam}`, async result => {
        if (result) {
            const ret = await fetch(Flask.url_for('api.registration_add'),
                {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({location_key: item, leerlingnummer: person.leerlingnummer})});
            const status = await ret.json();
            if (status.status) {
            } else {
                bootbox.alert(status.data)
            }
            ctx.reload_table();
        }
    });
}

$(document).ready(function () {
    let menu = [];
    for(const item of ctx.table_config.right_click) {
        menu.push({type: "item", iconscout: "plus-circle", label: `Nieuwe registratie: ${item.label}`, cb: ids => __registration_add(item.key, ids)});
        menu_item2label[item.key] = item.label;
    }
    create_context_menu(menu);

});
