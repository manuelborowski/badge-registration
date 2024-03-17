import { subscribe_right_click } from "../base/right_click.js";
import { ctx, get_data_of_row } from "../datatables/datatables.js"
import { formio_popup_create } from "../base/popup.js"

let menu_item2label = {};

const registration_add = async (item, ids) => {
   let person = get_data_of_row(ids[0]);
    bootbox.confirm(`${menu_item2label[item]}<br>Voor: ${person.naam} ${person.voornaam}`, async result => {
        if (result) {
            const ret = await fetch(Flask.url_for('api.registration_add'),
                {headers: {'x-api-key': api_key,}, method: 'POST', body: JSON.stringify({location_key: item, badge_code: person.rfid})});
            const status = await ret.json();
            if (status.status) {
            } else {
                bootbox.alert(status.data)
            }
            ctx.reload_table();
        }
    });
}


const export_items = ["sui-drank", "sui-kopies", "sul-drank", "sul-kopies", "sum-kopies"]

const export_student_balances_cb = (action, opaque, data=null) => {
    if (action === 'submit') {
        export_items.forEach(item => window.open(`/student/export/${item}/${data.startdate}/${data.enddate}`, '_blank'))
    }
}

const export_student_balances = (popup) => {
    console.log("yes")
    formio_popup_create(popup, export_student_balances_cb);
}


$(document).ready(function () {
    ctx.table_config.right_click.menu.forEach(menu_item => {
        subscribe_right_click(menu_item.item, (item, ids) => registration_add(item, ids));
        menu_item2label[menu_item.item] = menu_item.label;
    });
    subscribe_right_click('export-student-balance', (item, ids) => export_student_balances(ctx.popups['export-student-balance']));
});

