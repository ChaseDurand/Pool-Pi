document.addEventListener("DOMContentLoaded", function() {
    // Connect to the Socket.IO server.
    // The connection URL has the following format, relative to the current page:
    //     http[s]://<domain>:<port>[/<namespace>]
    var socket = io();

    // Diconnect callback function
    // This is called by the timeout function if a model hasn't been received recently
    function noConnection() {
        document.getElementsByClassName('overlay')[0].style.display = 'flex';
        document.getElementById('display1').innerHTML = '   NO CONNECTION    ';
        document.getElementById('display2').innerHTML = ' FROM RASPBERRY PI  ';
    }

    // Timeout ID for disconnect timer
    var timeoutID;

    // Disconnect timer function to notify user if connection has been lost
    // Reset when the model update is received
    function resetTimeout() {
        clearTimeout(timeoutID)
        timeoutID = window.setTimeout(
            function () {
                noConnection();
            }, 8000);
    }

    // Handler for the model update
    socket.on('model', function (msg) {
        resetTimeout();
        msgObj = JSON.parse(msg);
        // Parse display into two lines and blink if necessary
        len = msgObj['display_mask'].length;
        document.getElementById('display1').innerHTML = '';
        document.getElementById('display2').innerHTML = '';

        // Parse top row of display
        for (var i = 0; i < len / 2; ++i) {
            if (msgObj['display_mask'][i] == '1') {
                document.getElementById('display1').innerHTML += '<span class=' + 'blinkingText' + '>' + msgObj['display'].charAt(i) + '</span>';
            }
            else {
                document.getElementById('display1').innerHTML += msgObj['display'].charAt(i);
            }
        }
        // Parse bottom row of display
        for (var i = len / 2; i < len; ++i) {
            if (msgObj['display_mask'][i] == '1') {
                document.getElementById('display2').innerHTML += '<span class=' + 'blinkingText' + '>' + msgObj['display'].charAt(i) + '</span>';
            }
            else {
                document.getElementById('display2').innerHTML += msgObj['display'].charAt(i);
            }
        }
        delete msgObj['display'];
        delete msgObj['display_mask'];

        // Parse every item in json message
        for (var i = 0, len = Object.keys(msgObj).length; i < len; ++i) {
            attributeName = Object.keys(msgObj)[i];
            // Parse sending_message flag (no version)
            if (attributeName == 'sending_message') {
                if (msgObj[attributeName] == true) {
                    document.getElementsByClassName('overlay')[0].style.display = 'flex'
                }
                else {
                    document.getElementsByClassName('overlay')[0].style.display = 'none'
                }
                continue
            }

            // Parse service
            else if (attributeName == 'service') {
                if (msgObj['service'].state == 'ON') {
                    document.getElementById('service').parentElement.children['led'].className = 'LED red' + ' toggle-element';
                }
                else if (msgObj['service'].state == 'OFF') {
                    document.getElementById('service').parentElement.children['led'].className = 'LED off' + ' toggle-element';
                }
                else if (msgObj['service'].state == 'BLINK') {
                    document.getElementById('service').parentElement.children['led'].className = 'LED red blink' + ' toggle-element';
                }
                else if (msgObj['service'].state == 'INIT') {
                    document.getElementById('service').parentElement.children['led'].className = 'LED off' + ' toggle-element';
                }
            }

            // Parse pool/spa/spillover
            else if ((attributeName == 'pool') || (attributeName == 'spa') || (attributeName == 'spillover')) {
                if (msgObj[attributeName].state == 'ON') {
                    document.getElementById(attributeName).children['led'].className = 'LED green' + ' toggle-element';
                }
                else {
                    document.getElementById(attributeName).children['led'].className = 'LED off' + ' toggle-element';
                }
            }

            // Parse check system
            else if (attributeName == 'checksystem') {
                if (msgObj['checksystem'] == 'ON') {
                    document.getElementById('checksystem').className = 'LED orange';
                }
                else {
                    document.getElementById('checksystem').className = 'LED off';
                }
            }

            // Parse other buttons
            else {
                if (msgObj[attributeName].state == 'ON') {
                    document.getElementById(attributeName).parentElement.children['led'].className = 'LED green' + ' toggle-element';
                }
                else {
                    document.getElementById(attributeName).parentElement.children['led'].className = 'LED off' + ' toggle-element';
                }
            }

            // Update version
            document.getElementById(attributeName).setAttribute('version', msgObj[attributeName].version);
        }
    });

    // Handler for menu buttons
    document.querySelectorAll('.button-menu').forEach(element => element.addEventListener('click', function() {
        buttonID = this.getAttribute('id');
        socket.emit('command_event', { 'id': buttonID, 'data': 'na', 'version': '0', 'confirm': '0' });
    }));

    // Handler for toggle buttons
    document.querySelectorAll('.button-toggle').forEach(element => element.addEventListener('click', function() {
        // Double check that overlay is not present
        if (document.getElementsByClassName('overlay')[0].style.display != 'none') {
            return
        }
        document.getElementsByClassName('overlay')[0].style.display = 'flex';
        buttonID = this.getAttribute('id');
        buttonVersion = this.getAttribute('version');

        if (buttonID == 'pool-spa-spillover') {
            // Need to check which pool/spa/spillover is lit
            // Pool->Spa->Spillover
            if (!(document.getElementById('pool-spa-spillover').parentElement.parentElement.children['pool'].children['led'].classList.contains('off'))) {
                // Pool is on, need spa on
                buttonID = 'spa'
                targetState = 'ON';
            }
            else if (!(document.getElementById('pool-spa-spillover').parentElement.parentElement.children['spa'].children['led'].classList.contains('off'))) {
                // Spa is on, need spillover on
                buttonID = 'spillover'
                targetState = 'ON';
            }
            else if (!(document.getElementById('pool-spa-spillover').parentElement.parentElement.children['spillover'].children['led'].classList.contains('off'))) {
                // Spillover is on, need pool on
                buttonID = 'pool'
                targetState = 'ON';
            }
            else {
                // We haven't initialized yet
                targetState = 'INIT';
            }

        }
        else if (buttonID == 'service') {
            // Need to check if on/off/blinking
            if (document.getElementById(buttonID).parentElement.children['led'].classList.contains('off')) {
                // Currently off, need on
                targetState = 'ON';
            }
            else if (document.getElementById(buttonID).parentElement.children['led'].classList.contains('blink')) {
                // Currently blinking, target off
                targetState = 'OFF';
            }
            else {
                // Currently on, need blinking
                targetState = 'BLINK';
            }
        }
        else {
            // Need to check if on/off
            if (document.getElementById(buttonID).parentElement.children['led'].classList.contains('off')) {
                // Button is off, we need it on
                targetState = 'ON';
            }
            else {
                // Button is on, we need it off
                targetState = 'OFF';
            }
        }
        socket.emit('command_event', { 'id': buttonID, 'data': targetState, 'version': buttonVersion, 'confirm': '1' });
    }));
});