var xmlhttp = new XMLHttpRequest();
xmlhttp.onreadystatechange = function() {
	if (this.readyState == 4 && this.status == 200) {
		var myObj = JSON.parse(this.responseText);
		document.getElementById("coils").innerHTML = '<pre>' + JSON.stringify(myObj["coils"], undefined, 1).replace(/[{},]/g, '') + '</pre>';
		document.getElementById("holding-registers").innerHTML = '<pre>' + JSON.stringify(myObj["holdingRegisters"], null, 1).replace(/[{},]/g, '') + '</pre>';
		document.getElementById("discrete-inputs").innerHTML = '<pre>' + JSON.stringify(myObj["discreteInputs"], null, 1).replace(/[{},]/g, '') + '</pre>';
		document.getElementById("input-registers").innerHTML = '<pre>' + JSON.stringify(myObj["inputRegisters"], null, 1).replace(/[{},]/g, '') + '</pre>';
		document.getElementById("timestamp").innerHTML = '<pre>' + JSON.stringify(myObj["timestamp"], null, 1).replace(/[{},]/g, '') + '</pre>';

	}
};


function updatePage() {
	xmlhttp.open("GET", './modbus.json', true);
	xmlhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
	xmlhttp.send();
}

setInterval(updatePage,1000);