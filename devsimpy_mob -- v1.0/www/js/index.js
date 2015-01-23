var key = "";
// var address = "http://lcapocchi.pythonanywhere.com/";

var app = {
    // Application Constructor
    initialize: function() {
        this.bindEvents();
    },
    // Bind Event Listeners
    //
    // Bind any events that are required on startup. Common events are:
    // 'load', 'deviceready', 'offline', and 'online'.
    bindEvents: function() {
        document.addEventListener('deviceready', this.onDeviceReady, false);
    },
    // deviceready Event Handler
    //
    // The scope of 'this' is the event. In order to call the 'receivedEvent'
    // function, we must explicitly call 'app.receivedEvent(...);'
    onDeviceReady: function() {
        app.receivedEvent('deviceready');
    },
    // Update DOM on a Received Event
    receivedEvent: function(id) {
        var parentElement = document.getElementById(id);
        var listeningElement = parentElement.querySelector('.listening');
        var receivedElement = parentElement.querySelector('.received');

        listeningElement.setAttribute('style', 'display:none;');
        receivedElement.setAttribute('style', 'display:block;');

        console.log('Received Event: ' + id);
    }
};

app.initialize();


function createCORSRequest(method, url) {
    var xhr = new XMLHttpRequest();
    if ("withCredentials" in xhr) {

        // Check if the XMLHttpRequest object has a "withCredentials" property.
        // "withCredentials" only exists on XMLHTTPRequest2 objects.
        xhr.open(method, url, true);

    } else if (typeof XDomainRequest != "undefined") {

        // Otherwise, check if XDomainRequest.
        // XDomainRequest only exists in IE, and is IE's way of making CORS requests.
        xhr = new XDomainRequest();
        xhr.open(method, url);

    } else {

        // Otherwise, CORS is not supported by the browser.
        xhr = null;

    }
    return xhr;
}


function getParameterByName(param)
{
    var results = new RegExp('[\?&]' + param + '=([^&#]*)').exec(window.location.href);
    if (results==null){
       return null;
    } else {
        return results[1] || 0;
    }
}  

function renderView(controller) {
    if (!controller) {
        controller = getParameterByName("view");
    }
    if (controller){
        $("#container").load("views/modules/"+controller+".html");
    } else {
        renderView("home");
    }
};
function session_reg(ip) {
    if (sessionStorage !== null) {
        sessionStorage.setItem('ip', ip);
        // connect();
        if (is_connected()) {
            alert("Well connected!");
        }
    } else {
        alert('Session storage not supported!');
    }
};

function is_connected() {
    is_connected = false;
    if (sessionStorage.getItem('ip') !== null)  {
        is_connected = true;
    }
    return is_connected;
};

function session_get() {
    if (sessionStorage.ip !== "") {
        var session_ip = sessionStorage.getItem('ip');
        var session_host = session_ip
    } else {
        alert('Session storage not supported!');
    }
};

function list_dsp(data){
    var items = [];
    // $.each( data, function( key, val ) {
        // items.push(
        //     "<li class='table-view-cell media'>\
        //         <a class='navigate-right' onClick=\"document.location.href='index.html?dsp.html?view=dsp&dsp="+key+"'\" data-transition='slide-in'>\
        //             <img class='media-object pull-left' src='http://placehold.it/42x42'>\
        //             <div class='media-body'>\
        //             "+key+"\
        //             <p>"+val[1].description+"</p>\
        //             </div>\
        //         </a>\
        //     </li>" );
    // });
    
    $.each(data['content'], function(key, val){
        items.push(
            "<li class='table-view-cell media'>\
                <a class='navigate-right' onClick=\"document.location.href='index.html?dsp.html?view=dsp&dsp="+key+"'\" data-transition='slide-in'>\
                    <div class='media-body'>\
                    "+key+"\
                    </div>\
                </a>\
            </li>" );
    });

    $("<ul/>", {
        "class": "table-view",
        html: items.join( "" )
    }).appendTo( "#content-padded" );
};

function parse_dsp(data, dsp){

    $("#header").html("<a class='navigate-left' onClick=\"window.location='index.html?view=listing_dsp'\" data-transition='slide-out'><h3 class='center'>"+dsp+"</h3></a>");

    var obj = data[dsp];
    // var atomic_models = obj[0].models[0].atomic_models;
    // var coupled_models = obj[0].models[0].coupled_models;
    // var connections = obj[0].models[0].connections;
    var cells = obj[0];
    var description = obj[1].description;

    $("#footer").html(
        "<button id='simulate' class='btn btn-block'>Simulate</button>\
        <br>\
        <h4>Description</h4>\
        <p>"+description+"</p>"
        );

    draw(cells);
};

function discon(){
    // disconnect();
    delete sessionStorage.ip;
    sessionStorage.clear();
    alert('Disconnected!');
};

function draw(json) {
    var graph = new joint.dia.Graph;

    var paper = new joint.dia.Paper({
        el: $('#paper'),
        width: $(document).width()-20,
        height: $(document).height()-($("#head").height()+$("#header").height()+$("#footer").height()),
        gridSize: 1,
        model: graph,
        perpendicularLinks: true
    });

    graph.fromJSON(json);
    paper.scaleContentToFit();
    paper.setOrigin(paper.options.origin["x"], 50);
    // console.log(paper.options.origin);
}


function stub(d) {
    console.log(d);
};

function onConnect(k) {
    console.log('Established connection with ', k);
    key = k;
};

function connect() {
    window.tlantic.plugins.socket.connect(onConnect, stub, sessionStorage.getItem('ip'), 80);
    //window.tlantic.plugins.socket.connect(stub, stub, host, 18004);
};

function send(data) {
    window.tlantic.plugins.socket.send(stub, stub, key, data);
};

function disconnect() {
    window.tlantic.plugins.socket.disconnect(stub, stub, sessionStorage.getItem('ip')+':80');
};

function disconnectAll() {
    window.tlantic.plugins.socket.disconnectAll(stub, stub);
};

function isConnected() {
    window.tlantic.plugins.socket.isConnected(key, stub, stub);
};


function simulate(dsp_name) {
    var url = sessionStorage.ip+"simulate?name="+dsp_name+"&time=10";

    var xhr = createCORSRequest('GET', url);
    if (!xhr) {
        throw new Error('CORS not supported');
    }

    xhr.onload = function() {
        var responseText = xhr.responseText;
        $("#header").html("<a class='navigate-left' onClick=\"window.location='index.html?view=dsp&dsp="+dsp_name+"'\" data-transition='slide-out'><h3 class='center'>Simulation Result</h3></a>");
        console.log(responseText);
        // process the response.
        $("#result").html(responseText);
    };

    xhr.onerror = function(err) {
        console.log('There was an error!');
    };

    xhr.send();
};



$(document).ready(function(){

    // $.ajaxSetup({ cache: false });

    $('body').on('click', 'a', renderView());

    if (is_connected()) {

        session_get();

        $("<span id='listing_dsp' class='icon icon-list pull-left'></span>").appendTo("#head");
        $(document).on('click', '#listing_dsp', (function(){
            window.location = "index.html?view=listing_dsp";
        }));

        $('#con').html("<button class='btn btn-link btn-nav pull-right' id='disconnect' type='submit'>Disconnect <span class='icon icon-gear'></span></button>");
        $("body").on('click', '#disconnect', function(event){
            discon();
        });

        var controller = getParameterByName("view");
        if (controller !== "listing_dsp" && controller !== "dsp") {
            renderView();
        } else if (controller == "listing_dsp") {
            renderView("listing_dsp");
            $.getJSON(sessionStorage.ip+"yaml?all")
                .done(function(data){
                    list_dsp(data);
                })
                .fail(function( jqxhr, textStatus, error ) {
                    var err = textStatus + ", " + error;
                    console.log( "Request Failed: " + err );
            });
        } else if (controller == "dsp") {
            renderView(controller);
            var dsp = getParameterByName("dsp");

            $.getJSON(sessionStorage.ip+"json?name="+dsp)
                .done(function(data){
                    parse_dsp(data, dsp);
                })
                .fail(function( jqxhr, textStatus, error ) {
                        var err = textStatus + ", " + error;
                        console.log( "Request Failed: " + err );
            });

            $('body').on('click', '#simulate', function(event){
                renderView("result");
                simulate(dsp);
            });
        }
        
        document.addEventListener(window.tlantic.plugins.socket.receiveHookName, function (ev) {
            console.log('Data has been received: ', JSON.stringify(ev.metadata));
            alert(ev.metadata.data);
            var p = JSON.parse(ev.metadata.data);
                console.log(p);
            });

    } else {

        $('#con').html("<button class='btn btn-link btn-nav pull-right' name='view' value='connect' type='submit'>Connect <span class='icon icon-gear'></span></button>");
        renderView();

        $('body').on('submit', '#connection', function(event){
            var address = 'http://'+$("#ip").val()+'/';
            if (address == '') {
                alert("Please enter the IP adress!");
                event.preventDefault();
            } else {
                session_reg(address);
            }
        });
    }


});
