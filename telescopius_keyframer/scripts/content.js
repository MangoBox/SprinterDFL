const { core, studio } = Theatre

studio.initialize();
var sim;
var obj;
var sheet;
var startTries = 10;
var tries = startTries;
function waitForElement() {
    console.log('Waiting for element...');
    sim = document?.querySelector("#dsoApp")
            ?.shadowRoot
            ?.querySelector("#pageWrapper > tlc-page-telescope-simulator")
            ?.shadowRoot
            ?.querySelector("#planetarium")
            ?.shadowRoot
            ?.querySelector("#telescopeSimulator");
    if(sim) {
        //We're done!
        console.log("Found the Telescope Simulator. Starting the extension.");
        main();
        return;
    }
    tries--;
    if(tries == 0) {
        console.log('Element not found after ' +startTries + ' tries. Exiting.');
        return;
    }
    setTimeout(waitForElement, 500);   
}
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function main() {
    console.log("Starting the extension.");
    //Add the button to the UI
    const project = core.getProject('Sprinter Keyframer')
    sheet = project.sheet('Camera')
    obj = sheet.object('Keyframes', {
        ra: core.types.number(1, { range: [0, 24] }),
        dec: core.types.number(1, { range: [-90, 90] }),
        focalLength: core.types.number(1, { range: [16, 300] }),
    })

    obj.onValuesChange((obj) => {
        sim.ra = obj.ra;
        sim.dec = obj.dec;
        sim.telescopeFocalLength = obj.focalLength;
        //sequence.__experimental_getKeyframes(obj.props.position.x);
        console.log(sheet.sequence);
    })

    // const simProxy = new Proxy(sim, {
    //     set: function (target, key, value) {
    //      console.log(`${key} set from ${obj.foo} to ${value}`);
    //      target[key] = value;
    //      return true;
    //    },
    // });
}
async function exportJSON() {
    // console.log(sim);
    max_time = 7;
    fps = 12;
    times = Array.from({length: max_time * fps}, (_, i) => i / fps);
    console.log(times);
    csv_out = "RA,DEC,FL\n";
    for(var i = 0; i < times.length; i++) {
        time = times[i];
        sheet.sequence.position = time;
        ra = core.val(obj.props.ra).toFixed(6);
        dec = core.val(obj.props.dec).toFixed(6);
        focalLength = core.val(obj.props.focalLength).toFixed(2);
        console.log(ra, dec, focalLength);
        csv_out += `${ra},${dec},${focalLength}\n`;
    }
    console.log(csv_out);
}

// Wait for the element on startup.
waitForElement();