import {return_render_ellipsis} from "./dataTables.ellipsis.js";
import {MakeCellsToggleable} from "./dataTables.cellToggle.js";
import {busy_indication_on, busy_indication_off} from "../base/base.js";
import { socketio } from "../base/socketio.js";
import { subscribe_get_ids, set_endpoint } from "../base/right_click.js";

let filter_settings = [];
let column_name_to_index = {};
const filters = table_config.filters;

export let ctx = null;

//If not exactly one checkbox is selected, display warning and return false, else return true
function is_exactly_one_checkbox_selected() {
    let nbr_checked = 0;
    $(".chbx_all").each(function () {
        if (this.checked) {
            nbr_checked++;
        }
    });
    if (nbr_checked === 1) {
        return true;
    } else {
        bootbox.alert("U moet exact één item selecteren");
        return false;
    }
}

//If one or more checkboxes are checked, return true.  Else display warning and return false
function is_at_least_one_checkbox_selected() {
    let nbr_checked = 0;
    $(".chbx_all").each(function () {
        if (this.checked) {
            nbr_checked++;
        }
    });
    if (nbr_checked === 0) {
        bootbox.alert("U hebt niets geselecteerd, probeer nogmaals");
        return false;
    } else {
        return true;
    }
}

export function get_id_of_checked_boxes() {
    let ids = [];
    const chbxs = document.querySelectorAll('.chbx_all:checked')
    chbxs.forEach(chbx => {
        ids.push(chbx.value);
    });
    return ids;
}

export function clear_checked_boxes() {
    $(".chbx_all").prop('checked', false);
    $("#select_all").prop('checked', false);
}

export function get_data_of_row(id) {
    return ctx.table.row(`#${id}`).data();
}


export function update_cell(row_id, column_name, value) {
    let row_idx = ctx.table.row(`#${row_id}`).index();
    let column_idx = column_name_to_index[column_name];
    ctx.table.cell(row_idx, column_idx).data(value);
}

function button_pushed(action) {
    switch (action) {
        case 'delete':
            if (is_at_least_one_checkbox_selected()) {
                let message = table_config.delete_message;
                bootbox.confirm(message, function (result) {
                    if (result) {
                        const ids = get_id_of_checked_boxes();
                        location.href = Flask.url_for(table_config.table_action, {action: 'delete', ids: JSON.stringify(ids)})
                    }
                });
            }
            break
        case 'edit':
            if (is_exactly_one_checkbox_selected()) {
                const id = document.querySelector('.chbx_all:checked').value
                location.href = Flask.url_for(table_config.table_action, {action: 'edit', ids: JSON.stringify([id])})
            }
            break
        case 'add':
            location.href = Flask.url_for(table_config.table_action, {action: 'add'})
            break
        case 'view':
            if (is_exactly_one_checkbox_selected()) {
            }
            break
    }
}

export function clear_filter_setting() {
    localStorage.clear(`Filter-${ctx.table_config.view}`);
    location.reload();
}

function reload_table() {
    ctx.table.ajax.reload();
}


const get_ids_of_selected_items = mouse_event => {
    var ids = get_id_of_checked_boxes();
    if (ids.length === 0) {
        ids = [mouse_event.target.parentElement.id];
    }
    return ids;
}


$(document).ready(function () {
    ctx = {
        table_config,
        filters,
        popups,
        current_user_is_at_least_admin,
        reload_table
    }
    ctx.cell_to_color = "color_keys" in table_config ? table_config.cell_color.color_keys : null;
    ctx.suppress_cell_content = "color_keys" in table_config ? table_config.cell_color.supress_cell_content : null;

    //configure right_click
    set_endpoint(table_config.right_click.endpoint);
    subscribe_get_ids(get_ids_of_selected_items);

    //if a filter is changed, then the filter is applied by simulating a click on the filter button
    $(".table-filter").change(function () {
        store_filter_settings();
        ctx.table.ajax.reload();
    });

    //Store locally in the client-browser
    function store_filter_settings() {
        filter_settings = [];
        if (filters.length > 0) {
            filters.forEach(f => {
                if (f.type === 'select') {
                    filter_settings.push({
                        name: f.name,
                        type: f.type,
                        value: document.querySelector(`#${f.name} option:checked`).value
                    });
                } else if (f.type === 'checkbox') {
                    let boxes = [];
                    f.boxes.forEach(([k, l]) => {
                        boxes.push({id: k, checked: document.querySelector(`#${k}`).checked})
                    });
                    filter_settings.push({
                        name: f.name,
                        type: f.type,
                        value: boxes
                    })
                }
            });
            localStorage.setItem(`Filter-${ctx.table_config.view}`, JSON.stringify(filter_settings));
        }
    }

    function load_filter_settings() {
        if (filters.length === 0) return true;
        filter_settings = JSON.parse(localStorage.getItem(`Filter-${ctx.table_config.view}`));
        if (!filter_settings) {
            filter_settings = [];
            return false
        }
        filter_settings.forEach(f => {
            if (f.type === 'select') {
                document.querySelector(`#${f.name}`).value = f.value;
            }
        })
        return true;
    }

    if (!load_filter_settings()) store_filter_settings(); //filters are applied when the page is loaded for the first time

    //Bugfix to repeat the table header at the bottom
    $("#datatable").append(
        $('<tfoot/>').append($("#datatable thead tr").clone())
    );

    let config_columns_cache = {}; //'data' is key, add sequence-number
    $.each(ctx.table_config.template, function (i, v) {
        v.idx = i
        config_columns_cache[v.data] = v;
    });

    $.each(ctx.table_config.template, function (i, v) {
        //ellipsis
        if ("ellipsis" in v) {
            let cutoff = v.ellipsis.cutoff;
            let wordbreak = v.ellipsis.wordbreak;
            v.render = return_render_ellipsis(cutoff, wordbreak, true);
        } else if ("bool" in v) {
            v.render = function (data, type, full, meta) {
                return data === true ? `<input type="checkbox" checked disabled/>` : '';
                // let is_checked = data === true ? "checked" : "";
                // return `<input type="checkbox" ${is_checked}/>`;
            };
        }
        column_name_to_index[v.data] = i;
    });

    //configure cell edit
    let celledit_inputtypes = [];
    let celledit_columns = []
    let celledit_select = {}
    let celltoggle_columns = []
    for (let i = 0; i < ctx.table_config.template.length; i++) {
        let options = [];
        if ("celledit" in ctx.table_config.template[i]) {
            if (ctx.table_config.template[i].celledit.type === 'select') {
                celledit_select[i] = {};
                ctx.table_config.template[i].celledit.options.forEach(o => {
                    options.push({value: o[0], display: o[1]});
                    celledit_select[i][o[0]] = o[1];
                });
            }
            if (ctx.table_config.template[i].celledit.type === 'toggle') {
                celltoggle_columns.push(i)
            } else {
                const entry = {column: i, type: ctx.table_config.template[i].celledit.type, options}
                celledit_columns.push(i);
                celledit_inputtypes.push(entry);
            }
        }
    }

    let datatable_config = {
        serverSide: true,
        stateSave: true,
        ajax: {
            url: Flask.url_for(table_config.table_ajax),
            type: 'POST',
            data: function (d) {
                return $.extend({}, d, {'filter': JSON.stringify(filter_settings)});
            }
        },
        pagingType: "full_numbers",
        columns: ctx.table_config.template,
        language: {url: "//cdn.datatables.net/plug-ins/2.1.8/i18n/nl-NL.json"},
        initComplete: function (settings, json) { //intercept flash messages when the table is loaded
            if ('flash' in json) {
                bootbox.alert(json['flash'].toString());
            }
        },
        createdRow: function (row, data, dataIndex, cells) {
            if (data.overwrite_row_color && data.overwrite_row_color !== "") {
                $(row).attr("style", "background-color: " + data.overwrite_row_color + ";");
            }
            if (data.overwrite_cell_color && data.overwrite_cell_color.length > 0) {
                data.overwrite_cell_color.forEach(([cn, cc]) => {
                    const ci = column_name_to_index[cn];
                    $(cells[ci]).attr("style", `background-color: ${cc};`);
                })
            }
        },
        rowCallback: function (row, data, displayNum, displayIndex, dataIndex) {
            if (data.row_action !== null) {
                row.cells[0].innerHTML = `<input type='checkbox' class='chbx_all' name='chbx' value='${data.row_action}'>` +
                    `<div value='${data.row_action}' class='pencil glyphicon glyphicon-pencil'></div>`;

            }
            if (celledit_select) {
                for ([column, select] of Object.entries(celledit_select)) {
                    row.cells[column].innerHTML = select[row.cells[column].innerHTML]
                }
            }
        },
        preDrawCallback: function (settings) {
            busy_indication_on();
        },
        drawCallback: function (settings) {
            let api = this.api();
            busy_indication_off();
            if (ctx.cell_to_color) {
                ctx.table.cells().every(function () {
                    if (this.data() in ctx.cell_to_color) {
                        $(this.node()).css("background-color", ctx.cell_to_color[this.data()]);
                        if (ctx.suppress_cell_content) {
                            $(this.node()).html("");
                        }
                    }
                });
            }
            if (table_config.buttons.includes("edit")) {
                //pencil is clicked
                $(".pencil").click(function () {
                    const activity_id = $(this).attr("value");
                    const checkbox = $("input[name$='chbx'][value=" + activity_id + "]");
                    checkbox.prop('checked', true);
                    edit_item();
                });
            }
            cell_toggle.display();

            let json = api.ajax.json();
            if ('show_info' in json && json.show_info.length > 0) {
                let show_info_div = document.querySelector(".show-info");
                show_info_div.innerHTML = '';
                json.show_info.forEach(i => {
                    show_info_div.innerHTML += `<div class="p-2 border">${i}</div>`
                });
            }
        },
    }

    if (table_config.suppress_dom) {
        datatable_config["filter"] = false;
        datatable_config["paging"] = false;
    } else {
        datatable_config["dom"] = "ifptlp";
    }

    if (current_user_is_at_least_admin) {
        datatable_config["lengthMenu"] = [50, 200, 500, 2000];
    } else {
        datatable_config["lengthMenu"] = [50, 200, 500, 2000];
    }

    if ("default_order" in table_config) {
        datatable_config["order"] = [[table_config.default_order[0], table_config.default_order[1]]];
    }

    if ("width" in table_config) {
        $("#datatable").attr("width", table_config.width);
    }

    ctx.table = $('#datatable').DataTable(datatable_config);

    //double click a row to edit
    ctx.table.on('dblclick', 'tr', function () {
        document.querySelector(`input[value="${this.id}"]`).checked = true;
        button_pushed('edit');
    });

    //Toggle column visibility
    let column_visible_div = document.querySelector('.column-visible-div');
    let column_visible_settings = JSON.parse(localStorage.getItem(`ColumnsVisible-${ctx.table_config.view}`));
    if (!column_visible_settings || column_visible_settings.length !== ctx.table_config.template.length) {
        column_visible_settings = []
        ctx.table_config.template.forEach((column, i) => {
            column_visible_settings.push({data: column.data, visible: column.visible});
        });
        localStorage.setItem(`ColumnsVisible-${ctx.table_config.view}`, JSON.stringify(column_visible_settings));
    }
    column_visible_settings.forEach((column, i) => {
        if (column.visible !== 'never') {
            const config_column = config_columns_cache[column.data];
            let a = document.createElement('p');
            a.appendChild(document.createTextNode(`${config_column.name}`));
            if ('tt' in config_column) {
                a.setAttribute("title", config_column.tt);
            }
            a.setAttribute("data-column", i);
            a.setAttribute("class", column.visible === 'yes' ? "column-visible-a" : "column-invisible-a")
            ctx.table.column(i).visible(column.visible === 'yes');
            a.addEventListener('click', e => {
                e.preventDefault();
                let c = ctx.table.column(e.currentTarget.dataset['column']);
                c.visible(!c.visible());
                e.currentTarget.classList.toggle('column-invisible-a')
                e.currentTarget.classList.toggle('column-visible-a')
                column_visible_settings[e.currentTarget.dataset.column].visible = c.visible() ? 'yes' : 'no';
                localStorage.setItem(`ColumnsVisible-${ctx.table_config.view}`, JSON.stringify(column_visible_settings));
            });
            column_visible_div.appendChild(a);
        }
    });

    function cell_edit_cb(type, data) {
        if ("status" in data) {
            if (data.status) {
                ctx.table.ajax.reload();
            }
        } else if ("reload-table" in data) {
            ctx.table.ajax.reload();
        }
    }

    if ('socketio_endpoint' in table_config) {
        socketio.subscribe_on_receive(table_config.socketio_endpoint, cell_edit_cb);
        socketio.start(null, null);
    }


    function update_cell_changed(data) {
        if ('socketio_endpoint' in table_config) {
            socketio.send_to_server(table_config.socketio_endpoint, data);
        } else {
            $.getJSON(Flask.url_for("{{table_config.cell_endpoint}}", {'jds': JSON.stringify(data)}),
                function (data) {
                    if (data.status) {
                        ctx.table.ajax.reload();
                    } else {
                        bootbox.alert('Fout: kan waarde niet aanpassen');
                    }
                }
            );
        }
    }

    function cell_edit_changed_cb(cell, row, old_value) {
        const column = cell.index().column;
        let value = ctx.table_config.template[column].celledit.type.includes('int') ? parseInt(cell.data()) : cell.data();
        let column_name = ctx.table.column(column).dataSrc()
        let data = {id: row.data().DT_RowId, column: column_name, value}
        update_cell_changed(data);
    }

    function cell_toggle_changed_cb(cell, row, value) {
        data = {
            'id': row.data().DT_RowId,
            'column': cell.index().column,
            'value': value
        }
        update_cell_changed(data);
    }

    if (celledit_inputtypes.length > 0) {
        // ctx.table.MakeCellsEditable("destroy");
        ctx.table.MakeCellsEditable({
            onUpdate: cell_edit_changed_cb,
            columns: celledit_columns,
            inputTypes: celledit_inputtypes,
            inputCss: "celledit-input"
        });
    }

    let cell_toggle = new MakeCellsToggleable(ctx.table, {
        onUpdate: cell_toggle_changed_cb,
        columns: celltoggle_columns
    })

    if ("row_detail" in table_config) {
        //For an extra-measure, show the associated remarks as a sub-table
        let d_table_start = '<table cellpadding="5" cellspacing="0" border="2" style="padding-left:50px;">'
        let d_table_stop = '</table>'
        let d_header = '<tr><td>Datum</td><td>Leerling</td><td>LKR</td><td>KL</td><td>Les</td><td>Opmerking</td><td>Maatregel</td></tr>'

        function format_row_detail(data) {
            let s = d_table_start;
            s += d_header;
            if (data) {
                for (let i = 0; i < data.length; i++) {
                    s += '<tr>'
                    s = s + '<td>' + data[i].date + '</td>';
                    s = s + '<td>' + data[i].student.full_name + '</td>';
                    s = s + '<td>' + data[i].teacher.code + '</td>';
                    s = s + '<td>' + data[i].grade.code + '</td>';
                    s = s + '<td>' + data[i].lesson.code + '</td>';
                    s = s + '<td>' + data[i].subjects + '</td>';
                    s = s + '<td>' + data[i].measures + '</td>';
                    s += '</tr>'
                }
                s += d_table_stop;
                return s;
            }
            return 'Geen gegevens';
        }

        // Array to track the ids of the details displayed rows
        let detail_rows_cache = [];

        $('#datatable tbody').on('click', 'tr td.details-control', function () {
            let tr = $(this).closest('tr');
            let row = ctx.table.row(tr);
            let idx = $.inArray(tr.attr('DT_RowId'), detail_rows_cache);

            if (row.child.isShown()) {
                tr.removeClass('details');
                row.child.hide();
                detail_rows_cache.splice(idx, 1);
            } else {
                let tx_data = {"id": row.data().DT_RowId};
                $.getJSON(Flask.url_for('reviewed.get_row_detail', {'data': JSON.stringify(tx_data)}),
                    function (rx_data) {
                        if (rx_data.status) {
                            row.child(format_row_detail(rx_data.details)).show();
                            tr.addClass('details');
                            if (idx === -1) {
                                detail_rows_cache.push(tr.attr('DT_RowId'));
                            }
                        } else {
                            bootbox.alert('Fout: kan details niet ophalen');
                        }
                    });
            }
        });
    }

    if ("row_detail" in table_config) {
        //This function is called, each time the table is drawn
        ctx.table.on('draw', function () {
            //Row details
            $.each(detail_rows_cache, function (i, id) {
                $('#' + id + ' td.details-control').trigger('click');
            });
        });
    }

    //checkbox in header is clicked
    $("#select_all").change(function () {
        $(".chbx_all").prop('checked', this.checked);
    });

});

