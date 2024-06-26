import { subscribe_right_click } from "../base/right_click.js";
import { ctx, get_data_of_row } from "../datatables/datatables.js"

let menu_item2label = {};

const registration_add = async (item, ids) => {
   let person = get_data_of_row(ids[0]);
    bootbox.confirm(`${menu_item2label[item]}<br>Voor: ${person.naam} ${person.voornaam}`, async result => {
        if (result) {
            const ret = await fetch(Flask.url_for('api.registration_add'),
                {headers: {'x-api-key': ctx.api_key,}, method: 'POST', body: JSON.stringify({location_key: item, badge_code: person.rfid})});
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
    ctx.table_config.right_click.menu.forEach(menu_item => {
        subscribe_right_click(menu_item.item, (item, ids) => registration_add(item, ids));
        menu_item2label[menu_item.item] = menu_item.label;
    });
});

