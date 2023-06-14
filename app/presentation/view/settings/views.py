from flask import render_template
from flask_login import login_required

from app import admin_required
from app.application import socketio as msocketio
from . import settings
from app.application import settings as msettings, cron as mcron, formio as mformio, cron_table
import json

@settings.route('/settings', methods=['GET', 'POST'])
@admin_required
@login_required
def show():
  cron_module_enable_settings = msettings.get_configuration_setting('cron-enable-modules')
  cron_module = mformio.search_component(settings_formio, 'cron-enable-modules')
  cron_module["components"] = []
  for nbr, module in enumerate(cron_table):
    enabled = cron_module_enable_settings[module[0]] if module[0] in cron_module_enable_settings else False
    cron_module["components"].append({"label": f'({nbr+1}) {module[2]}', "tooltip": module[3], "tableView": False, "defaultValue": enabled, "key": module[0], "type": "checkbox", "input": True})
  default_settings = msettings.get_configuration_settings(convert_to_string=True)
  data = {'default': default_settings, 'template': settings_formio}
  return render_template('/settings/settings.html', data=data)


def update_settings_cb(msg, client_sid=None):
  try:
    data = msg['data']
    settings = json.loads(data['value'])
    msettings.set_setting_topic(settings)
    msocketio.broadcast_message({'type': 'settings', 'data': {'status': True}})
  except Exception as e:
    msocketio.broadcast_message({'type': 'settings', 'data': {'status': False, 'message': str(e)}})


msocketio.subscribe_on_type('settings', update_settings_cb)


from app.presentation.view import false, true, null

# https://formio.github.io/formio.js/app/builder
settings_formio = \
  {
    "display": "form",
    "components": [
      {
        "title": "Templates",
        "theme": "warning",
        "collapsible": true,
        "key": "templates",
        "type": "panel",
        "label": "Panel",
        "collapsed": true,
        "input": false,
        "tableView": false,
        "components": [
          {
            "label": "Users",
            "tableView": false,
            "key": "users",
            "type": "container",
            "input": true,
            "components": [
              {
                "title": "Gebruikers",
                "theme": "primary",
                "collapsible": true,
                "key": "gebruikers",
                "type": "panel",
                "label": "Algemeen",
                "collapsed": true,
                "input": false,
                "tableView": false,
                "components": [
                  {
                    "label": "Opslaan",
                    "showValidations": false,
                    "theme": "warning",
                    "tableView": false,
                    "key": "submit",
                    "type": "button",
                    "input": true,
                    "saveOnEnter": false
                  },
                  {
                    "label": "Lijst template (JSON)",
                    "autoExpand": false,
                    "tableView": true,
                    "key": "user-datatables-template",
                    "type": "textarea",
                    "input": true
                  }
                ]
              }
            ]
          },
          {
            "label": "History",
            "tableView": false,
            "key": "history",
            "type": "container",
            "input": true,
            "components": [
              {
                "title": "Historiek",
                "theme": "primary",
                "collapsible": true,
                "key": "historiek",
                "type": "panel",
                "label": "Algemeen",
                "collapsed": true,
                "input": false,
                "tableView": false,
                "components": [
                  {
                    "label": "Opslaan",
                    "showValidations": false,
                    "theme": "warning",
                    "tableView": false,
                    "key": "submit",
                    "type": "button",
                    "input": true,
                    "saveOnEnter": false
                  },
                  {
                    "label": "Lijst template (JSON)",
                    "autoExpand": false,
                    "tableView": true,
                    "key": "history-datatables-template",
                    "type": "textarea",
                    "input": true
                  }
                ]
              }
            ]
          },
          {
            "label": "Popups",
            "tableView": false,
            "key": "popups",
            "type": "container",
            "input": true,
            "components": [
              {
                "title": "Popups",
                "theme": "primary",
                "collapsible": true,
                "key": "RegistratieTemplate1",
                "type": "panel",
                "label": "Studenten",
                "collapsed": true,
                "input": false,
                "tableView": false,
                "components": [
                  {
                    "label": "Opslaan",
                    "showValidations": false,
                    "theme": "warning",
                    "tableView": false,
                    "key": "submit",
                    "type": "button",
                    "input": true,
                    "saveOnEnter": false
                  },
                  {
                    "label": "Nieuwe gebruiker / gebruiker aanpassen",
                    "autoExpand": false,
                    "tableView": true,
                    "key": "popup-new-update-user",
                    "type": "textarea",
                    "input": true
                  }
                ]
              }
            ]
          }
        ]
      },
      {
        "title": "Modules",
        "theme": "warning",
        "collapsible": true,
        "key": "modules",
        "type": "panel",
        "label": "Panel",
        "input": false,
        "tableView": false,
        "components": [
          {
            "label": "generic",
            "tableView": false,
            "key": "generic",
            "type": "container",
            "input": true,
            "components": [
              {
                "title": "Algemeen",
                "theme": "primary",
                "collapsible": true,
                "key": "algemeen",
                "type": "panel",
                "label": "Smartschool",
                "collapsed": true,
                "input": false,
                "tableView": false,
                "components": [
                  {
                    "label": "Opslaan ",
                    "showValidations": false,
                    "theme": "warning",
                    "tableView": false,
                    "key": "submit",
                    "type": "button",
                    "input": true
                  },
                  {
                    "label": "Registreer-badge-popup vertraging (ms)",
                    "labelPosition": "left-left",
                    "tooltip": "Hoe lang (in ms) blijft de popup zichtbaar wanneer een badge wordt geregistreerd",
                    "tableView": true,
                    "defaultValue": "1000",
                    "persistent": false,
                    "key": "generic-register-popup-delay",
                    "type": "textfield",
                    "labelWidth": 40,
                    "input": true
                  },
                  {
                    "label": "Nieuwe gebruikers via smartschool login?",
                    "tooltip": "Mogen nieuwe gebruikers inloggen via de Smartschool OAuth2?",
                    "tableView": false,
                    "key": "generic-new-via-smartschool",
                    "type": "checkbox",
                    "input": true,
                    "defaultValue": false
                  },
                  {
                    "label": "Nieuwe gebruikers via Smartschool: standaard niveau",
                    "labelPosition": "left-left",
                    "widget": "choicesjs",
                    "tooltip": "Standaard niveau wanneer een gebruiker voor de eerste maal aanmeldt via Smartschool OAuth2",
                    "tableView": true,
                    "defaultValue": 1,
                    "data": {
                      "values": [
                        {
                          "label": "Gebruiker",
                          "value": "1"
                        },
                        {
                          "label": "Gebruiker+",
                          "value": "2"
                        },
                        {
                          "label": "Toezichthouder",
                          "value": "3"
                        },
                        {
                          "label": "Toezichthouder+",
                          "value": "4"
                        },
                        {
                          "label": "Administrator",
                          "value": "5"
                        }
                      ]
                    },
                    "key": "generic-new-via-smartschool-default-level",
                    "type": "select",
                    "input": true,
                    "labelWidth": 60
                  }
                ]
              }
            ]
          },
          {
            "label": "Cron-generic",
            "tableView": false,
            "key": "cron-generic",
            "type": "container",
            "input": true,
            "components": [
              {
                "title": "Cron: generiek",
                "theme": "primary",
                "collapsible": true,
                "key": "cron-generic",
                "type": "panel",
                "label": "Smartschool",
                "collapsed": true,
                "input": false,
                "tableView": false,
                "components": [
                  {
                    "label": "Opslaan ",
                    "showValidations": false,
                    "theme": "warning",
                    "tableView": false,
                    "key": "submit",
                    "type": "button",
                    "input": true
                  },
                  {
                    "label": "Cron template",
                    "labelPosition": "left-left",
                    "tooltip": "Check https://crontab.guru/ voor de layout van de cron template",
                    "tableView": true,
                    "persistent": false,
                    "key": "cron-scheduler-template",
                    "type": "textfield",
                    "labelWidth": 20,
                    "input": true
                  },
                  {
                    "label": "Columns",
                    "columns": [
                      {
                        "components": [
                          {
                            "label": "Start cron cyclus",
                            "tableView": false,
                            "defaultValue": false,
                            "key": "check-start-cron-cycle",
                            "type": "checkbox",
                            "input": true
                          }
                        ],
                        "width": 3,
                        "offset": 0,
                        "push": 0,
                        "pull": 0,
                        "size": "md",
                        "currentWidth": 3
                      },
                      {
                        "components": [
                          {
                            "label": "Start cron cyclus",
                            "showValidations": false,
                            "theme": "danger",
                            "tableView": false,
                            "key": "button-start-cron-cycle",
                            "conditional": {
                              "show": true,
                              "when": "cron-generic.check-start-cron-cycle",
                              "eq": "true"
                            },
                            "type": "button",
                            "saveOnEnter": false,
                            "input": true
                          }
                        ],
                        "width": 6,
                        "offset": 0,
                        "push": 0,
                        "pull": 0,
                        "size": "md",
                        "currentWidth": 6
                      }
                    ],
                    "key": "columns",
                    "type": "columns",
                    "input": false,
                    "tableView": false
                  },
                  {
                    "label": "Container",
                    "tableView": false,
                    "key": "cron-enable-modules",
                    "type": "container",
                    "input": true,
                    "components": []
                  }
                ]
              }
            ]
          },
          {
            "label": "Locations",
            "tableView": false,
            "key": "locations",
            "type": "container",
            "input": true,
            "components": [
              {
                "title": "Locaties",
                "theme": "primary",
                "collapsible": true,
                "key": "locations",
                "type": "panel",
                "label": "Cardpresso",
                "collapsed": true,
                "input": false,
                "tableView": false,
                "components": [
                  {
                    "label": "Opslaan ",
                    "showValidations": false,
                    "theme": "warning",
                    "tableView": false,
                    "key": "submit",
                    "type": "button",
                    "input": true
                  },
                  {
                    "label": "Locaties",
                    "tooltip": "Een JSON lijst van locaties",
                    "autoExpand": false,
                    "tableView": true,
                    "key": "location-profiles",
                    "type": "textarea",
                    "input": true
                  },
                  {
                    "label": "Artikels",
                    "tooltip": "Een JSON lijst van artikels",
                    "applyMaskOn": "change",
                    "autoExpand": false,
                    "tableView": true,
                    "key": "artikel-profiles",
                    "type": "textarea",
                    "input": true
                  }
                ]
              }
            ]
          },
          {
            "label": "sdh",
            "tableView": false,
            "key": "sdh2",
            "type": "container",
            "input": true,
            "components": [
              {
                "title": "School Data Hub",
                "theme": "primary",
                "collapsible": true,
                "key": "sdh",
                "type": "panel",
                "label": "Smartschool",
                "collapsed": true,
                "input": false,
                "tableView": false,
                "components": [
                  {
                    "label": "Opslaan ",
                    "showValidations": false,
                    "theme": "warning",
                    "tableView": false,
                    "key": "submit",
                    "type": "button",
                    "input": true
                  },
                  {
                    "label": "URL voor ophalen studenten",
                    "tableView": true,
                    "persistent": false,
                    "key": "sdh-student-url",
                    "type": "textfield",
                    "labelWidth": 20,
                    "input": true
                  },
                  {
                    "label": "URL voor ophalen groottes van studentenfoto's",
                    "tableView": true,
                    "persistent": false,
                    "key": "sdh-photo-size-url",
                    "type": "textfield",
                    "labelWidth": 20,
                    "input": true
                  },
                  {
                    "label": "URL voor ophalen van studentenfoto's",
                    "tableView": true,
                    "persistent": false,
                    "key": "sdh-photo-url",
                    "type": "textfield",
                    "labelWidth": 20,
                    "input": true
                  },
                  {
                    "label": "Columns",
                    "columns": [
                      {
                        "components": [
                          {
                            "label": "Toon sleutel",
                            "tableView": false,
                            "defaultValue": false,
                            "key": "sdh-show-key",
                            "type": "checkbox",
                            "input": true
                          }
                        ],
                        "width": 2,
                        "offset": 0,
                        "push": 0,
                        "pull": 0,
                        "size": "md",
                        "currentWidth": 2
                      },
                      {
                        "components": [
                          {
                            "label": "API sleutel",
                            "tableView": true,
                            "key": "sdh-api-key",
                            "conditional": {
                              "show": true,
                              "when": "sdh2.sdh-show-key",
                              "eq": "true"
                            },
                            "type": "textfield",
                            "input": true
                          }
                        ],
                        "width": 5,
                        "offset": 0,
                        "push": 0,
                        "pull": 0,
                        "size": "md",
                        "currentWidth": 5
                      }
                    ],
                    "key": "columns",
                    "type": "columns",
                    "input": false,
                    "tableView": false
                  }
                ]
              }
            ]
          },
          {
            "label": "API",
            "tableView": false,
            "key": "api1",
            "type": "container",
            "input": true,
            "components": [
              {
                "title": "API",
                "theme": "primary",
                "collapsible": true,
                "key": "api",
                "type": "panel",
                "label": "Cardpresso",
                "collapsed": true,
                "input": false,
                "tableView": false,
                "components": [
                  {
                    "label": "Opslaan ",
                    "showValidations": false,
                    "theme": "warning",
                    "tableView": false,
                    "key": "submit",
                    "type": "button",
                    "input": true
                  },
                  {
                    "label": "API sleutels",
                    "tooltip": "Een JSON lijst van sleutels",
                    "autoExpand": false,
                    "tableView": true,
                    "key": "api-keys",
                    "type": "textarea",
                    "input": true
                  },
                  {
                    "label": "Schoolrekening info pagina (HTML)",
                    "applyMaskOn": "change",
                    "autoExpand": false,
                    "tableView": true,
                    "key": "api-schoolrekening-info",
                    "type": "textarea",
                    "input": true
                  }
                ]
              }
            ]
          },
          {
            "label": "Emailserver",
            "tableView": false,
            "key": "emailserver",
            "type": "container",
            "input": true,
            "components": [
              {
                "title": "E-mail server instellingen",
                "theme": "primary",
                "collapsible": true,
                "key": "emailserver",
                "type": "panel",
                "label": "E-mail server settings",
                "input": false,
                "tableView": false,
                "components": [
                  {
                    "label": "Submit",
                    "showValidations": false,
                    "theme": "warning",
                    "tableView": false,
                    "key": "submit",
                    "type": "button",
                    "input": true
                  },
                  {
                    "label": "Aantal keer dat een e-mail geprobeerd wordt te verzenden",
                    "labelPosition": "left-left",
                    "mask": false,
                    "spellcheck": false,
                    "tableView": false,
                    "delimiter": false,
                    "requireDecimal": false,
                    "inputFormat": "plain",
                    "key": "email-send-max-retries",
                    "type": "number",
                    "input": true
                  },
                  {
                    "label": "Tijd (seconden) tussen het verzenden van e-mails",
                    "labelPosition": "left-left",
                    "mask": false,
                    "spellcheck": true,
                    "tableView": false,
                    "persistent": false,
                    "delimiter": false,
                    "requireDecimal": false,
                    "inputFormat": "plain",
                    "key": "email-task-interval",
                    "type": "number",
                    "input": true
                  },
                  {
                    "label": "Max aantal e-mails per minuut",
                    "labelPosition": "left-left",
                    "mask": false,
                    "spellcheck": true,
                    "tableView": false,
                    "persistent": false,
                    "delimiter": false,
                    "requireDecimal": false,
                    "inputFormat": "plain",
                    "key": "emails-per-minute",
                    "type": "number",
                    "input": true
                  },
                  {
                    "label": "Basis URL",
                    "labelPosition": "left-left",
                    "tableView": true,
                    "key": "email-base-url",
                    "type": "textfield",
                    "input": true
                  },
                  {
                    "label": "E-mails mogen worden verzonden",
                    "tableView": false,
                    "persistent": false,
                    "key": "email-enable-send-email",
                    "type": "checkbox",
                    "input": true,
                    "defaultValue": false
                  }
                ],
                "collapsed": true
              }
            ]
          },
          {
            "label": "Logging",
            "tableView": false,
            "key": "logging",
            "type": "container",
            "input": true,
            "components": [
              {
                "title": "Logging",
                "theme": "primary",
                "collapsible": true,
                "key": "logging",
                "type": "panel",
                "label": "E-mail server settings",
                "collapsed": true,
                "input": false,
                "tableView": false,
                "components": [
                  {
                    "label": "Submit",
                    "showValidations": false,
                    "theme": "warning",
                    "tableView": false,
                    "key": "submit",
                    "type": "button",
                    "input": true
                  },
                  {
                    "label": "Logs met niveau ERROR worden verstuurd naar volgende adressen",
                    "tooltip": "één adres per rij\nEen adres wordt niet gebruikt als er een # voor staat",
                    "autoExpand": false,
                    "tableView": true,
                    "key": "logging-inform-emails",
                    "type": "textarea",
                    "input": true
                  }
                ]
              }
            ]
          }
        ],
        "collapsed": true
      }
    ]
  }