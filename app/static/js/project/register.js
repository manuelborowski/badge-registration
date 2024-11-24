import {rfidusb_set_location, subscribe_location_changed} from "./rfidusb.js";

$(document).ready(function () {
    rfidusb_set_location("timeregistration");
});


