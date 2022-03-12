var xmlhttp = new XMLHttpRequest();
xmlhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        refreshPage(JSON.parse(this.responseText))
    }
};

function signalType(signals, tableName) {
    return `
  <div id="customers">
    <table class="signal-list">
      <caption class="signal-type-title">${tableName}</caption>
      <thead>
        <tr>
          <th>Register</th>
          <th>Bit</th>
          <th>Type</th>
          <th>Name</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        ${signals.map(signal => `
        <tr>
          <td>${signal.address.register}</td>
          <td>${signal.address.absolute}</td>
          <td>${signal.type}</td>
          <td>${signal.name}</td>
          <td>${signal.value}</td>
        </tr>`).join('')}
      </tbody>
    </table>
   </div>
  `
}


var refreshPage = function(modbusData) {

	const coils = modbusData.signals.filter(signal => signal.type==="coil")
	const holdingRegisters = modbusData.signals.filter(signal => signal.type==="holdingRegister")
	const discreteInputs = modbusData.signals.filter(signal => signal.type==="discreteInput")
	const inputRegisters = modbusData.signals.filter(signal => signal.type==="inputRegister")
	const outputs = coils.concat(holdingRegisters)
	const inputs = discreteInputs.concat(inputRegisters)

	document.getElementById("app").innerHTML = `
	<div class="timestamp">
		<strong>Timestamp:</strong> ${modbusData.timestamp}
	</div>
	
	<div class="row">
		<div class="column signalbox">
			${signalType(outputs, "From master to slave")}
		</div>
		<div class="column signalbox">
			${signalType(inputs, "From slave to master")}
		</div>
	</div>
	`;
};


function updatePage() {
    xmlhttp.open("GET", 'http://localhost:8080/signals', true);
    xmlhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xmlhttp.send();
}


let intervalHandle

function updateGetDataInterval(element) {
	if (element.value > 100) 
	{
		clearInterval(intervalHandle)
		intervalHandle = setInterval(updatePage, element.value);
	} else if (element.value < 100) {
		element.value = 100;
	}
}


function initApp() {
	updatePage()
	
	window.addEventListener('load', function () {

		intervalHandle = setInterval(updatePage, document.getElementById("update-interval").value);
	})


}

initApp()