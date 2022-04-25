var path = "./QC/";
var subjects = [];
var subjstatus = [];
var clocks = 0;
var currentSubject = -1;
var brainsuiteRunParameters;
var expanded = false;
var intervalID = null;
var enableHover = true;
var completed = "⚫";
var launched = "🔵";
var queued = "⚪";
var errorcode = "🔴";
var updateInterval = 200;
var wrapImages = false;
//var pixel = '1x1-00000000.png';
//var pixel='<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==">'
var pixel='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'

var expandSubject = null;
var slideHeight = 256;
var expandAll = false;
var enableLazyLoad = true;
var showAnnotations = false;
var hideUnlaunched = false;
var expand=null;

function setUpdateInterval(t) {
    updateInterval = t;
    if (intervalID) {
        clearInterval(intervalID);
        intervalID = setInterval(updateState, updateInterval);
    }
}

function downloadTextAsFile(filename, text, mimeType) {
    var link = document.createElement('a');
    mimeType = mimeType;// || 'text/plain';
    link.setAttribute('download', filename);
    link.setAttribute('href', 'data:' + mimeType + ';charset=utf-8,' + text);
    link.click();
}

function exportAnnotations() {
    var sep = '\t';//    sep=','; can be easily switched to CSV if necessary
    var data = "participant_id" + sep + "Exclude" + sep + "Note\n";
    for (var sid = 0; sid < subjects.length; sid++) {
        var subject = subjects[sid];
        var excludeCB = document.getElementById('excl-' + sid);
        var exclude = (excludeCB && excludeCB.checked) ? 1 : 0;
        var noteField = document.getElementById('note-' + sid);
        var note = (noteField != null) ? noteField.value : "";
        data += subject + sep + exclude + sep + '"' + note + '"\n';
    }
    downloadTextAsFile("BrainSuiteQCExcludeList.tsv", encodeURI(data), 'tab-separated-values');
    //    downloadTextAsFile("BrainSuiteQCExcludeList.csv",encodeURI(data),'text/csv');
}

//text/csv

const blueSquare = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t9f/2/16/1f7e6.png';//🟦
const brownSquare = 'https://static.xx.fbcdn.net/images/emoji.php/v9/tcb/2/16/1f7eb.png';//🟫
const greenSquare = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t22/2/16/1f7e9.png';//🟩
const orangeSquare = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t20/2/16/1f7e7.png';//🟧
const purpleSquare = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t4a/2/16/1f7ea.png';//🟪
const redSquare = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t1e/2/16/1f7e5.png';//🟥
const yellowSquare = 'https://static.xx.fbcdn.net/images/emoji.php/v9/ta1/2/16/1f7e8.png';//🟨
const whiteSquare = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t6c/2/16/2b1c.png';//⬜
const blackSquare = 'https://static.xx.fbcdn.net/images/emoji.php/v9/teb/2/16/2b1b.png';
const blueCircle = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t8e/2/16/1f535.png';//
const brownCircle = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t9d/2/16/1f7e4.png';//🟫
const greenCircle = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t9b/2/16/1f7e2.png';//🟩
const orangeCircle = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t99/2/16/1f7e0.png';//🟧
const purpleCircle = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t1c/2/16/1f7e3.png';//🟪
const redCircle = 'https://static.xx.fbcdn.net/images/emoji.php/v9/td/2/16/1f534.png';//🟥//
const yellowCircle = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t1a/2/16/1f7e1.png';//🟨
const whiteCircle = 'https://static.xx.fbcdn.net/images/emoji.php/v9/te/2/16/26aa.png';//⬜
const blackCircle = 'https://static.xx.fbcdn.net/images/emoji.php/v9/t8f/2/16/26ab.png';

function handleWrapImagesClick(cb) { wrapImages = cb.checked; refillSubjectRows(true); }
function handleEnableHoverClick(cb) { enableHover = cb.checked; refillSubjectRows(); }
function handleEnableLazyLoad(cb) { enableLazyLoad = cb.checked; refillSubjectRows(); }
function handleShowAnnotationsClick(cb) { showAnnotations = cb.checked; updateAnnotations(); }


function updateDisplayedSubjects() {
    if (subjects != null)
        for (var sid = 0; sid < subjects.length; sid++) {
            var subject = subjects[sid];
            if (subjstatus[sid] == null) continue;
            if (subjstatus[sid][0] == 'N') {
                var div = document.getElementById('d' + sid);
                if (div != null) div.style.display = (hideUnlaunched) ? "none" : "block";
            }
        }
}

function handleHideUnlaunched(cb) {
    hideUnlaunched = cb.checked;
    updateDisplayedSubjects();
}

function toggleUpdates() {
    var pauseButton = document.getElementById("pause");
    if (intervalID == null) {
        intervalID = setInterval(updateState, updateInterval);
        pauseButton.innerHTML = '<i class="fa-solid fa-pause" aria-hidden="true"></i> Pause';
    }
    else {
        clearInterval(intervalID);
        intervalID = null;
        pauseButton.innerHTML = '<i class="fa-solid fa-play" aria-hidden="true"></i> Resume';

    }
}

function showCheckboxes() {
    var checkboxes = document.getElementById("checkboxes");
    if (!expanded) {
        checkboxes.style.display = "block";
        expanded = true;
    } else {
        checkboxes.style.display = "none";
        expanded = false;
    }
}

var groupNames = ["CSE", "Thickness", "SVReg", "BDP", "BFP"];
var stagenames = ["bse", "bfc", "pvc", "cerebro", "cortex", "scrub mask", "tca", "dewisp", "inner cortical surface", "pial surface", "hemisplit", "thickness", "svreg", "bdp", "bfp"];
var contents = [
    { img: "bse.png", stage: 1, desc: "Orig + BSE Mask", group: 0, surface: false, show: true, width: 0, height: 0 },
    { img: "bfc.png", stage: 2, desc: "BFC", group: 0, surface: false, show: true, width: 0, height: 0 },
    { img: "pvc.png", stage: 3, desc: "PVC", group: 0, surface: false, show: true, width: 0, height: 0 },
    { img: "hemilabel.png", stage: 4, desc: "Orig + Hemi Label ", group: 0, surface: false, show: true, width: 0, height: 0 },
    { img: "cerebro.png", stage: 4, desc: "Orig + Cerebrum Mask", group: 0, surface: false, show: true, width: 0, height: 0 },
    { img: "dewisp.png", stage: 8, desc: "BFC + Dewisp (axial)", group: 0, surface: false, show: true, width: 0, height: 0 },
    { img: "dewispCor.png", stage: 8, desc: "BFC + Dewisp (coronal)", group: 0, surface: false, show: true, width: 0, height: 0 },
    { img: "dfsLeft.png", stage: 9, desc: "Inner Cortex (left)", group: 0, surface: true, show: true, width: 256, height: 256 },
    { img: "dfsRight.png", stage: 9, desc: "Inner Cortex (right)", group: 0, surface: true, show: true, width: 256, height: 256 },
    { img: "dfsSup.png", stage: 9, desc: "Inner Cortex (superior)", group: 0, surface: true, show: true, width: 256, height: 256 },
    { img: "dfsInf.png", stage: 9, desc: "Inner Cortex (inferior)", group: 0, surface: true, show: true, width: 256, height: 256 },
    { img: "hemisplit.png", stage: 11, desc: "Pial Cortex (HemiSplit)", group: 0, surface: true, show: true, width: 256, height: 256 },
    { img: "ThickdfsLeft.png", stage: 12, desc: "Thickness PVC (left)", group: 1, surface: true, show: true, width: 256, height: 256 },
    { img: "ThickdfsRight.png", stage: 12, desc: "Thickness PVC (right)", group: 1, surface: true, show: true, width: 256, height: 256 },
    { img: "ThickdfsSup.png", stage: 12, desc: "Thickness PVC (sup)", group: 1, surface: true, show: true, width: 256, height: 256 },
    { img: "ThickdfsInf.png", stage: 12, desc: "Thickness PVC (inf)", group: 1, surface: true, show: true, width: 256, height: 256 },
    { img: "SVREGdfsLeft.png", stage: 13, desc: "SVReg Mid Cortex (left)", group: 2, surface: true, show: true, width: 256, height: 256 },
    { img: "SVREGdfsRight.png", stage: 13, desc: "SVReg Mid Cortex (right)", group: 2, surface: true, show: true, width: 256, height: 256 },
    { img: "SVREGdfsSup.png", stage: 13, desc: "SVReg Mid Cortex (inferior)", group: 2, surface: true, show: true, width: 256, height: 256 },
    { img: "SVREGdfsInf.png", stage: 13, desc: "SVReg Mid Cortex (superior)", group: 2, surface: true, show: true, width: 256, height: 256 },
    { img: "SVREGdfsAnt.png", stage: 13, desc: "SVReg Mid Cortex (anterior)", group: 2, surface: true, show: true, width: 256, height: 256 },
    { img: "SVREGdfsPos.png", stage: 13, desc: "SVReg Mid Cortex (posterior)", group: 2, surface: true, show: true, width: 256, height: 256 },
    { img: "svregLabel.png", stage: 13, desc: "BFC + SVReg Label (axial)", group: 2, surface: false, show: true, width: 0, height: 0 },
    { img: "svregLabelCor.png", stage: 13, desc: "BFC + SVReg Label (coronal)", group: 2, surface: false, show: true, width: 0, height: 0 },
    { img: "svregLabelSag.png", stage: 13, desc: "BFC + SVReg Label (sagittal)", group: 2, surface: false, show: true, width: 0, height: 0 },
    { img: "PreCorrDWI.png", stage: 14, desc: "PRECORRECT", group: 3, surface: false, show: true, width: 256, height: 0 },
    { img: "PreCorrDWIsag.png", stage: 14, desc: "PRECORRECT", group: 3, surface: false, show: true, width: 256, height: 0 },
    { img: "PostCorrDWI.png", stage: 14, desc: "POSTCORRECT", group: 3, surface: false, show: true, width: 256, height: 0 },
    { img: "PostCorrDWIsag.png", stage: 14, desc: "POSTCORRECT", group: 3, surface: false, show: true, width: 256, height: 0 },
    { img: "FApvc.png", stage: 14, desc: "FA PVC", surface: false, group: 3, show: true, width: 0, height: 0 },
    { img: "FA.png", stage: 14, desc: "FA", group: 3, surface: false, show: true, width: 0, height: 0 },
    { img: "colorFA.png", stage: 14, desc: "COLOR FA", group: 3, surface: false, show: true, width: 0, height: 0 },
    { img: "mADC.png", stage: 14, desc: "mADC", group: 3, surface: false, show: true, width: 0, height: 0 },
    { img: "ssim.png", stage: 15, desc: "SSIM", group: 4, surface: false, show: true, width: 256, height: 0 },
    { img: "mco.png", stage: 15, desc: "MCO", group: 4, surface: false, show: true, width: 256, height: 0 },
    { img: "Func2T1.png", stage: 15, group: 4, desc: "FUNC2T1 T1 MASK", surface: false, show: true, width: 0, height: 0 },
    { img: "PreCorrFunc.png", stage: 15, group: 4, desc: "PRECORRECT", surface: false, show: true, width: 0, height: 0 },
    { img: "PreCorrFuncSag.png", stage: 15, group: 4, desc: "PRECORRECT", surface: false, show: true, width: 0, height: 0 },
    { img: "PostCorrFunc.png", stage: 15, group: 4, desc: "POSTCORRECT", surface: false, show: true, width: 0, height: 0 },
    { img: "PostCorrFuncSag.png", stage: 15, group: 4, desc: "POSTCORRECT", surface: false, show: true, width: 0, height: 0 },
];

function progressBar(stagecodes, showAll = false) {
    if (stagecodes == null) return;
    if (stagecodes[stage] == 'N') return "queued for launch.";
    const notrun = (showAll) ? "&#x1F916" : "";
    var bar = "";
    for (var stage = 0; stage < stagecodes.length; stage++) {
        var stagename = stagenames[stage];
        switch (stagecodes[stage]) {
            case 'L': bar += launched; break;
            case 'E': bar += errorcode; break;
            case 'Q': bar += queued; break;
            case 'C': bar += completed; break;
            case 'U': bar += notrun; break;
        }
    }
    return bar;
}

function showRunParameters() {
    var id=document.getElementById('RunParameters');
    if (!id) return;
    if (brainsuiteRunParameters != null) {
        var outHTML = "";
        var desc = brainsuiteRunParameters["DATASET DESCRIPTION"];
        // var runParameters = brainsuiteRunParameters["BrainSuite BIDS App run parameters"];
        outHTML += "<b>Dataset Name: </b>" + desc[0]["Dataset Name"] + "<br/>";
        // outHTML += "<b>BIDS Version: </b>" + desc[0]["BIDSVersion"] + "<br/>";
        id.innerHTML=outHTML
    }
    else id.innerHTML= "<b>BrainSuite Run Parameters unavailable.</b>";
    
}

function updateMenus() {

    var file = path + 'brainsuite_dashboard_config.json';
    $.ajax({
        cache: false,
        url: file,
        dataType: "json",
        success: function (data) {            
            if (data.Contents!=null) contents=data.Contents;
            if (data.StageNames!=null) stagenames=data.StageNames;
            if (data.GroupNames!=null) groupNames=data.GroupNames;
            $("#userGroupDbKeyAjax2").empty(); 
            buildStageMenus();
        },
        error: function() { buildStageMenus(); }
    });

}

function processStats()
{
    if (subjstatus==null) return;
    var nStatus=subjstatus.length;
    var nTotal=subjects.length;
    var s=nStatus +"/" + nTotal;
    var waiting=0;
    var finished=0;
    var error=0;
    var queued=0;
    var running=0;
    var other=0;
    for (var i=0;i<nStatus;i++)
    {
        var stagecodes=subjstatus[i];
        if (stagecodes[0]=='N') waiting++;
        else if (/^[CU]*$/.test(stagecodes)) finished++; // finished if all jobs are complete or not specified to run
        else if (/L/.test(stagecodes)) running++; // finished if all jobs are complete or not specified to run
        else if (/Q/.test(stagecodes)) queued++; // finished if all jobs are complete or not specified to run
        else other++;
        if (/E/.test(stagecodes)) error++; // finished if all jobs are complete or not specified to run
    }
    return "<span class='text-success'>finished: "+finished+"</span>"+
        " <span class='text-primary'>running: "+running+"</span>"+
        " <span class='text-danger'>error: "+error+"</span>"+
        " <span class='text-dark'>queued: "+queued+"</span>"+
        " <span class='text-muted'>waiting: "+waiting+"</span>"+
        "</br>";
}

function updateState() {
    clocks++;
    var file = path + 'brainsuite_state.json';
    $.ajax({
        cache: false,
        url: file,
        dataType: "json",
        success: function (data) {
            subjstatus = data.process_states;

            var payload = "";
            // payload += " status " + data.status + "<br/>";
            payload += " start time: " + data.start_time + "<br/>";
            payload += " last update: " + data.update_time + "<br/>";
            payload += " run time: " + data.runtime;
            payload += ((data.end) ? " (processing has concluded)" : " (processing is active)") + "<br/>";
            payload += processStats();
            document.getElementById("info").innerHTML = payload;
            refillSubjectRows();
        }
    });
    document.getElementById("session counter").innerHTML = "<b>browser session counter " + clocks + "</b>&nbsp&nbsp";
}

function checkboxClicked(cb) {
    contents[parseInt(cb.id)].show = cb.checked;
    refillSubjectRows();
}

function updateCheckboxes() {
    $("#qcColumnSelector").val([...new Set(contents.filter(e => e.show == true).map(function (e) { return e.index; }))]);
    $("#qcColumnSelector").multiselect("refresh");
}

var showSingleSubject = false;
function showSubjectBoard(subjectIndex) {
    if (currentSubject >= 0) {
        showSingleSubject ^= true;
        var btn = document.getElementById("showSubjectBoard");
        if (btn != null) btn.innerText = (showSingleSubject) ? "Show All Subjects" : "Show Single Subject";
        refillSubjectRows();
    }
}

function showGroup(group) {
    if (group < 0)
        for (var i = 0; i < contents.length; i++) contents[i].show = true;
    else
        for (var i = 0; i < contents.length; i++) contents[i].show = (contents[i].group == group);
    refillSubjectRows();
    updateCheckboxes();
}

function selectSubject(sid) {
    currentSubject = sid;
    if (subjects != null)
        for (var i = 0; i < subjects.length; i++) {
            var s = document.getElementById("status" + i);
            if (s != null) s.style.backgroundColor = (currentSubject == i) ? '#CCCCCC' : 'white';
        }
}

function selectSubjectToggle(sid) {
    selectSubject((sid != currentSubject) ? sid : -1);
}

function toggleExpandSubject(sid) {
    expandSubject = (expandSubject == null || expandSubject != sid) ? sid : null;
    if (expand!=null) expand[sid]^=true;
    refillSubjectRows();
}


function updateProgressBar() {
    if (subjects != undefined) {
        for (var sid = 0; sid < subjects.length; sid++) {
            var div = document.getElementById('status' + sid);
            if (div != null) div.innerHTML = makeSubjectStatusBar(sid);
        }
    }
}

function refillSubjectRows(flag) {
    if (subjects != undefined) {
        var divclass = ((wrapImages) ? 'sliderow-wrap' : 'sliderow');
        for (var sid = 0; sid < subjects.length; sid++) {
            var div = document.getElementById('status' + sid);
            if (div != null) div.innerHTML = makeSubjectStatusBar(sid);
            div = document.getElementById('row' + sid);
            if (div != null) {
                if (flag != null && flag) div.setAttribute('class', divclass);
                div.innerHTML = (
                    //expandAll || (expandSubject != null && sid == expandSubject)
                    expand[sid]
                ) ? generateSlideRow(sid) : "";
            }
        }
    }
}

function makeSubjectStatusBar(sid) {
    var stagecodes = subjstatus[sid];
    var subject = subjects[sid];
    var subjectLine = "<b>"
    +"<div onclick='toggleExpandSubject(" + sid + ");' style='float:left' >"
    + ((expand[sid]) ? '<i class="fa-solid fa-square-minus"></i>' : '<i class="fa-solid fa-square-plus"></i>')
    +"</div>"
    + "&nbsp" + subject;
    if (stagecodes == null) return subjectLine+"</b>&nbspstatus unavailable. &nbsp</B>";
    if (stagecodes[0] == 'N') return subjectLine+ "</b>&nbspwaiting to launch. &nbsp</B>";
    subjectLine += "</b>&nbsp" + progressBar(stagecodes) + "&nbsp";
    var allFinished = /^[CU]*$/.test(stagecodes); // finished if all jobs are complete or not specified to run
    var isWaiting = /Q/.test(stagecodes);
    var notRunning = /^[QUCE]*$/.test(stagecodes); // test if queued BUT NOT RUNNING
    var finishedWithError = true;
    for (var stage = 0; stage < stagecodes.length; stage++) if (stagecodes[stage] != 'C' && stagecodes[stage] != 'E') { finishedWithError = false; break; }
    var finishedOrWaiting = true;
    for (var stage = 0; stage < stagecodes.length; stage++) if (stagecodes[stage] != 'C' && stagecodes[stage] != 'Q') { finishedOrWaiting = false; break; }
    if (allFinished) { subjectLine += "<span class='desc text-success' style='color:green;'>finished all stages.</span>"; }
    else if (isWaiting && notRunning) { subjectLine += "<span class='desc' style='color:black;'>queued to run.</span>"; }
    else {
        var errors = "";
        for (var stage = 0; stage < stagecodes.length; stage++) {
            if (stagecodes[stage] == 'L') {
                subjectLine += "<span class='desc text-primary' style='color:blue'>running " + stagenames[stage] + ".</span>" + "&nbsp";
            }
            if (stagecodes[stage] == 'E') {
                if (errors.length > 0) errors += ", ";
                errors += stagenames[stage];
            }
        }
        if (errors.length > 0) subjectLine += "<span class='desc text-danger' style='color:red'>errors occurred running " + errors + "</span>";
    }
    return subjectLine;
}

function generateSlideRow(sid) {
    var slideHTML = "";
    var subject = subjects[sid];
    if (subjstatus[sid] == null) return "";
    if (subjstatus[sid][0] == 'N') return "";
    var loadingGIF = "<img width=25% SRC='https://c.tenor.com/hQz0Kl373E8AAAAi/loading-waiting.gif'>";
    var showCount = 0;
    if (contents.filter(e => e.show == true).length == 0) { return "no stages selected."; }
    for (var i = 0; i < contents.length; i++) {
        stage = contents[i].stage - 1;
        var stagecode = subjstatus[sid][stage];
        if (contents[i].show) {
            var image = pixel;
            var imagetext = null;
            var color = "grey";
            var bootcls = 'dark';
            var imgcls = 'slideImage';
            var para = "<p class='slidetext' style='font-size: " + slideHeight / 20 + "pt;'>";
            switch (stagecode) {
                case 'C': color = "green"; bootcls = 'success'; image = path + subject + "/" + contents[i].img; imgcls+=" zoom"; break;
                case 'L': color = "blue"; bootcls = 'primary'; imagetext = para + "running " + stagenames[stage] + "...</p><br/>" + loadingGIF; break;
                case 'Q': color = "black"; bootcls = 'dark'; imagetext = para + stagenames[stage] + " is queued</p>"; break;
                case 'E': color = "red"; bootcls = 'danger'; imagetext = para + "error in: " + stagenames[stage] + "</p>"; break;

                case 'U': continue;
                default: break;
            }
            var captionfont = "<p class='captiontext text-" + bootcls + " text-wrap' style='font-size: " + slideHeight / 22 + "pt; color:" + color + ";'>";
            slideHTML += "<div class='slide' >";
            slideHTML += "<div class='IMimage border border-" + bootcls + " style='border:1px solid " + color + "'>";
            slideHTML += "<a href=" + image + "><img";
            if (enableLazyLoad) slideHTML += " loading='lazy' alt='...'";
            slideHTML += " class='"+imgcls+"' src='" + image + "' height='" + slideHeight + "px' ></a>";
            if (imagetext != null) {
                slideHTML += "<div class='IMtext text-" + bootcls + " text-wrap' style='color:" + color + "'>" + imagetext + "</div>";
            }
            slideHTML += "</div>";
            slideHTML += "<div class='slidecaption border border-" + bootcls + "' style='border:1px solid " + color + "; vertical-align:bottom; text-align:center'>"
                + captionfont + contents[i].desc + "</p></div>";
            slideHTML += "</div>";
            showCount++;
        }
    }
    return (showCount > 0) ? slideHTML : "None of the selected outputs were specified for this subject."
}

function updateAnnotations() {
    for (var sid = 0; sid < subjects.length; sid++) {
        var div = document.getElementById('note' + sid);
        if (div != null) div.style.display = (showAnnotations) ? "block" : "none";
    }
}

function initContainers() {
    var subjectPanel = document.getElementById("subjectPanel");
    if (subjectPanel == null) return;
    if (subjects != undefined) {
        var divclass = ((wrapImages) ? 'sliderow-wrap' : 'sliderow');
        for (var sid = 0; sid < subjects.length; sid++) {
            var subject = subjects[sid];
            var subjectLine = "<div id='d" + sid + "'>";
            subjectLine += "<div id='status" + sid + "'"
//                +" onclick='selectSubjectToggle(" + sid + ");'"
                +" ondblclick='toggleExpandSubject(" + sid + ");'"
                +"></div>";
            if (showAnnotations)
                subjectLine += "<div id='note" + sid + "' style='display:block;'>";
            else
                subjectLine += "<div id='note" + sid + "' style='display:none;'>";
            subjectLine += "<span><input type='checkbox' name='subID' id='excl-" + sid + "'/>Exclude</span>";
            subjectLine += "&nbsp&nbsp<span><input size=50 type='text' placeholder='Note' class='exReason' id='note-" + sid + "'/></span>";
            subjectLine += "</div>";
            subjectLine += "<div class='" + divclass + "' id='row" + sid + "'></div>";
            subjectLine += "</div>";
            subjectPanel.innerHTML += subjectLine;
        }
    }
}

function updateHeightSlider(h) {
    setSlideHeight(h);
    var slider = document.getElementById("imageHeightSlider");
    if (slider != null) slider.value = h;
}

function setSlideHeight(h) {
    slideHeight = h;
    var images = document.querySelectorAll('.slideImage'), imageArray = Array.prototype.slice.call(images);
    imageArray.forEach(function (img) { img.style.height = slideHeight + 'px'; });//imageSize+'px'); });
    var slideText = document.querySelectorAll('.slidetext'), textArray = Array.prototype.slice.call(slideText);
    textArray.forEach(function (p) { p.style.fontSize = slideHeight / 20 + 'pt'; });
    var captionText = document.querySelectorAll('.captiontext'), textArray = Array.prototype.slice.call(captionText);
    textArray.forEach(function (p) { p.style.fontSize = slideHeight / 24 + 'pt'; });
}

function toggleExpandAll() {
    expandAll ^= true;
    refillSubjectRows();
    var button = document.getElementById("expand all");
    expand.fill(expandAll);
    if (button != null) button.innerHTML = (expandAll) ? '<i class="fa-solid fa-square-caret-up"></i> Collapse All' : '<i class="fa-solid fa-square-caret-down"></i> Expand All';
}

function setProgressCodes(C, L, Q, E) {
    completed = C;
    launched = L;
    queued = Q;
    errorcode = E;
}

function setColorSchemePng(C, L, Q, E) {
    completed = '<img height=14 width=14 src=' + C + '>';
    launched = '<img height=14 width=14 src=' + L + '>';
    queued = '<img height=14 width=14 src=' + Q + '>';
    errorcode = '<img height=14 width=14 src=' + E + '>';
}

function emojiButton(a, b, c, d, buttonText) {
    if (buttonText == null) buttonText = a + b + c + d;
    return '<button class="dropdown-item" onclick=" setProgressCodes(\'' + a + '\',\'' + b + '\',\'' + c + '\',\'' + d + '\');updateProgressBar();">' + buttonText + '</button>';
}

function pngButton(a, b, c, d, buttonText) {
    return '<button class="dropdown-item" onclick=" setColorSchemePng(\'' + a + '\',\'' + b + '\',\'' + c + '\',\'' + d + '\');updateProgressBar();">' + buttonText + '</button>';
}


function updateColumnSelectorGroups(id) {
    var element = document.getElementById(id);
    var groups = [...new Set(contents.map(function (e) { return e.group; }))];
    var html = "";
    var idx = 0;
    for (var i = 0; i < contents.length; i++) contents[i].index = i;
    for (var i = 0; i < groups.length; i++) {
        var g = groups[i];
        var a = contents.filter(e => e.group == groups[g]);
        var name = (groupNames[g]) ? groupNames[i] : "Group " + g;
        html += "<optgroup label='" + name + "' class='group-" + g + "'>\n";
        for (var j = 0; j < a.length; j++) {
            html += "\t<option value='" + a[j].index + "'";//+i+"."+j+"'";            
            if (contents[i].show) html += " selected='selected'";
            html += ">" + a[j].desc + "</option>\n";
        }
        html += "</optgroup>\n";
    }
    element.innerHTML = html;
    return;
}

function updateColumns() {
    contents.forEach(element => element.show = false);
    $('#qcColumnSelector').val().forEach(element => contents[element].show = true);
    refillSubjectRows();
}

function buildStageMenus()
{
    updateColumnSelectorGroups('qcColumnSelector');
    $('#qcColumnSelector').multiselect({
        enableClickableOptGroups: true,
        enableCollapsibleOptGroups: true,
        includeSelectAllOption: true,
        collapseOptGroupsByDefault: true,
        maxHeight: 400,
        onChange: function(option, checked, select) { updateColumns(); },
        onSelectAll: function(options) { updateColumns(); },
        onDeselectAll: function(options) { updateColumns(); },
        templates: {
            button: '<span class="multiselect dropdown-toggle text-primary border-primary btn" data-toggle="dropdown">'
                      +'<i class="fa-solid fa-gears"></i>'
                      +' Stages&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'+'<span class="d-none d-xl-block"></span>'
                      +'</span>'            
        }
    });
    var div=document.getElementById('pipelineDropdownMenuDiv');
    if (div!=null)
    {
        var s='<button id="showAll" class="dropdown-item btn-sm" onclick="showGroup(-1)">All</button>';
        for (var i=0;i<groupNames.length;i++)
            s+='<button id="'+groupNames[i]+'" class="dropdown-item btn-sm" onclick="showGroup('+i+')">'+groupNames[i]+'</button>';
        div.innerHTML=s;
    }
    updateCheckboxes();
}

$(function () {
    updateMenus();
    var buttonPanel = document.getElementById("scheme buttons");
    if (buttonPanel != null) {
        var s = "";
        s += emojiButton("⚫", "🔵", "⚪", "🔴");
        s += pngButton(blackCircle, blueCircle, whiteCircle, redCircle, "use png");
        s += emojiButton('💚', '💜', '💙', '💔');
        s += emojiButton('🧠', '🏃', '🤷', '🔥');
        s += emojiButton('🟩', '🟨', '⬛', '🟥', 'wrdl');
        s += pngButton(greenSquare, yellowSquare, blackSquare, redSquare, "wrdlpng");
        s += emojiButton("🟢", "🔵", "🟡", "🔴", "green emoji");
        s += pngButton(greenCircle, blueCircle, orangeCircle, redCircle, "green-blue png");
        s += pngButton(blueCircle, orangeCircle, whiteCircle, redCircle, "blue-orange png");
        s += '</div>';
        buttonPanel.innerHTML = s;
    }
    var slider = document.getElementById("imageHeightSlider");
    if (slider) {
        slider.value = slideHeight;
        slider.oninput = function () { setSlideHeight(this.value); }
    }
    setProgressCodes("⚫", "🔵", "⚪", "🔴");
    $.getJSON("QC/subjectIDs.json", function (data) {
        subjects = data.subjects;
        if (subjects != undefined) expand=Array(subjects.length).fill(false);
        initContainers();
    });
    $.getJSON("QC/brainsuite_run_params.json", function (data) { brainsuiteRunParameters = data; showRunParameters();});

    // updateColumnSelectorGroups('qcColumnSelector');
    // $('#qcColumnSelector').multiselect({
    //     enableClickableOptGroups: true,
    //     enableCollapsibleOptGroups: true,
    //     includeSelectAllOption: true,
    //     collapseOptGroupsByDefault: true,
    //     maxHeight: 400,
    //     onChange: function (option, checked, select) { updateColumns(); },
    //     onSelectAll: function (options) { updateColumns(); },
    //     onDeselectAll: function (options) { updateColumns(); },
    //     templates: {
    //         button: '<span class="multiselect dropdown-toggle text-primary border-primary btn" data-toggle="dropdown"><i class="fa-solid fa-gears"></i> Stages&nbsp&nbsp</span>'

    //     }
    // });
//    buildStageMenus();
    intervalID = setInterval(updateState, updateInterval);

});

