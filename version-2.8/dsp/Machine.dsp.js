title('Discrete Event System Specification');
description('Description du diagramme.');
dimension(1200,560);

var devs = Joint.dia.devs;
Joint.paper("world", 1480, 1480);

var NLFunction_13 = devs.Model.create({
	rect: {x: 40, y: 680, width: 130, height: 60},
	label: "NLFunction_13",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5","in6","in7"],
	oPorts: ["out0"]
});
var Rotor = devs.Model.create({
	rect: {x: 200, y: 40, width: 100, height: 60},
	label: "Rotor",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5"],
	oPorts: ["out0","out1","out2","out3","out4","out5"]
});
var FEM_R = devs.Model.create({
	rect: {x: 360, y: 40, width: 100, height: 60},
	label: "FEM_R",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5","in6","in7"],
	oPorts: ["out0","out1","out2"]
});
var FEM_S = devs.Model.create({
	rect: {x: 900, y: 360, width: 100, height: 60},
	label: "FEM_S",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5","in6","in7"],
	oPorts: ["out0","out1","out2"]
});
var LPF_2 = devs.Model.create({
	rect: {x: 820, y: 1000, width: 100, height: 60},
	label: "LPF_2",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var LPF_3 = devs.Model.create({
	rect: {x: 980, y: 1000, width: 100, height: 60},
	label: "LPF_3",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var WSum_1234 = devs.Model.create({
	rect: {x: 270, y: 520, width: 100, height: 60},
	label: "WSum_1234",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1"],
	oPorts: ["out0"]
});
var WSum_23 = devs.Model.create({
	rect: {x: 1010, y: 200, width: 100, height: 60},
	label: "WSum_23",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2"],
	oPorts: ["out0"]
});
var WSum_1111 = devs.Model.create({
	rect: {x: 1130, y: 840, width: 100, height: 60},
	label: "WSum_1111",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1"],
	oPorts: ["out0"]
});
var Integrator_333 = devs.Model.create({
	rect: {x: 1090, y: 1160, width: 130, height: 60},
	label: "Integrator_333",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Integrator_1234 = devs.Model.create({
	rect: {x: 40, y: 520, width: 170, height: 60},
	label: "Integrator_1234",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Integrator_23 = devs.Model.create({
	rect: {x: 230, y: 360, width: 130, height: 60},
	label: "Integrator_23",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Machine = devs.Model.create({
	rect: {x: 20, y: 20, width: 1440, height: 1440},
	label: "Machine",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "gray" },
	shadow: true,
});
var Tl = devs.Model.create({
	rect: {x: 430, y: 200, width: 100, height: 60},
	label: "Tl",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var WSum_333 = devs.Model.create({
	rect: {x: 40, y: 1320, width: 100, height: 60},
	label: "WSum_333",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1"],
	oPorts: ["out0"]
});
var WSum_222 = devs.Model.create({
	rect: {x: 390, y: 1320, width: 100, height: 60},
	label: "WSum_222",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1"],
	oPorts: ["out0"]
});
var SinGen3 = devs.Model.create({
	rect: {x: 520, y: 40, width: 100, height: 60},
	label: "SinGen3",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var SinGen2 = devs.Model.create({
	rect: {x: 680, y: 40, width: 100, height: 60},
	label: "SinGen2",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var SinGen1 = devs.Model.create({
	rect: {x: 840, y: 40, width: 100, height: 60},
	label: "SinGen1",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Integrator_11 = devs.Model.create({
	rect: {x: 1090, y: 680, width: 130, height: 60},
	label: "Integrator_11",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Integrator_2222 = devs.Model.create({
	rect: {x: 40, y: 1000, width: 170, height: 60},
	label: "Integrator_2222",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Integrator_3333 = devs.Model.create({
	rect: {x: 430, y: 1000, width: 170, height: 60},
	label: "Integrator_3333",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var WSum_3333 = devs.Model.create({
	rect: {x: 660, y: 1000, width: 100, height: 60},
	label: "WSum_3333",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1"],
	oPorts: ["out0"]
});
var Integrator_13 = devs.Model.create({
	rect: {x: 550, y: 840, width: 130, height: 60},
	label: "Integrator_13",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var WSum1 = devs.Model.create({
	rect: {x: 930, y: 1160, width: 100, height: 60},
	label: "WSum1",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4"],
	oPorts: ["out0"]
});
var WSum3 = devs.Model.create({
	rect: {x: 230, y: 1160, width: 100, height: 60},
	label: "WSum3",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4"],
	oPorts: ["out0"]
});
var WSum2 = devs.Model.create({
	rect: {x: 390, y: 1160, width: 100, height: 60},
	label: "WSum2",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4"],
	oPorts: ["out0"]
});
var NLFunction_11 = devs.Model.create({
	rect: {x: 420, y: 680, width: 130, height: 60},
	label: "NLFunction_11",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5","in6","in7"],
	oPorts: ["out0"]
});
var LPF_11 = devs.Model.create({
	rect: {x: 930, y: 680, width: 100, height: 60},
	label: "LPF_11",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var LPF_12 = devs.Model.create({
	rect: {x: 610, y: 680, width: 100, height: 60},
	label: "LPF_12",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var LPF_13 = devs.Model.create({
	rect: {x: 770, y: 680, width: 100, height: 60},
	label: "LPF_13",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var LPF2 = devs.Model.create({
	rect: {x: 580, y: 360, width: 100, height: 60},
	label: "LPF2",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var LPF3 = devs.Model.create({
	rect: {x: 420, y: 360, width: 100, height: 60},
	label: "LPF3",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Integrator_222 = devs.Model.create({
	rect: {x: 200, y: 1320, width: 130, height: 60},
	label: "Integrator_222",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var LPF1 = devs.Model.create({
	rect: {x: 740, y: 360, width: 100, height: 60},
	label: "LPF1",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var ConstGen2 = devs.Model.create({
	rect: {x: 1160, y: 40, width: 100, height: 60},
	label: "ConstGen2",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var ConstGen3 = devs.Model.create({
	rect: {x: 1000, y: 40, width: 100, height: 60},
	label: "ConstGen3",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Integrator_12 = devs.Model.create({
	rect: {x: 360, y: 840, width: 130, height: 60},
	label: "Integrator_12",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var ConstGen1 = devs.Model.create({
	rect: {x: 40, y: 200, width: 100, height: 60},
	label: "ConstGen1",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var WSum_56787 = devs.Model.create({
	rect: {x: 1290, y: 360, width: 130, height: 60},
	label: "WSum_56787",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1"],
	oPorts: ["out0"]
});
var Integrator_1111 = devs.Model.create({
	rect: {x: 900, y: 840, width: 170, height: 60},
	label: "Integrator_1111",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Electric_couple = devs.Model.create({
	rect: {x: 590, y: 200, width: 170, height: 60},
	label: "Electric_couple",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5","in6"],
	oPorts: ["out0"]
});
var WSum_2345 = devs.Model.create({
	rect: {x: 660, y: 520, width: 100, height: 60},
	label: "WSum_2345",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1"],
	oPorts: ["out0"]
});
var Integrator_2345 = devs.Model.create({
	rect: {x: 430, y: 520, width: 170, height: 60},
	label: "Integrator_2345",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Integrator2 = devs.Model.create({
	rect: {x: 550, y: 1160, width: 130, height: 60},
	label: "Integrator2",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var P = devs.Model.create({
	rect: {x: 1170, y: 200, width: 100, height: 60},
	label: "P",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Integrator1 = devs.Model.create({
	rect: {x: 740, y: 1160, width: 130, height: 60},
	label: "Integrator1",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var WSum_2222 = devs.Model.create({
	rect: {x: 270, y: 1000, width: 100, height: 60},
	label: "WSum_2222",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1"],
	oPorts: ["out0"]
});
var WSum_13 = devs.Model.create({
	rect: {x: 200, y: 840, width: 100, height: 60},
	label: "WSum_13",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4"],
	oPorts: ["out0"]
});
var WSum_12 = devs.Model.create({
	rect: {x: 40, y: 840, width: 100, height: 60},
	label: "WSum_12",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4"],
	oPorts: ["out0"]
});
var WSum_11 = devs.Model.create({
	rect: {x: 740, y: 840, width: 100, height: 60},
	label: "WSum_11",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4"],
	oPorts: ["out0"]
});
var NLFunction_6 = devs.Model.create({
	rect: {x: 820, y: 520, width: 130, height: 60},
	label: "NLFunction_6",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5","in6","in7"],
	oPorts: ["out0"]
});
var NLFunction_5 = devs.Model.create({
	rect: {x: 1010, y: 520, width: 130, height: 60},
	label: "NLFunction_5",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5","in6","in7"],
	oPorts: ["out0"]
});
var Stator = devs.Model.create({
	rect: {x: 40, y: 40, width: 100, height: 60},
	label: "Stator",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5"],
	oPorts: ["out0","out1","out2","out3","out4","out5"]
});
var NLFunction_3 = devs.Model.create({
	rect: {x: 1200, y: 520, width: 130, height: 60},
	label: "NLFunction_3",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5","in6","in7"],
	oPorts: ["out0"]
});
var Integrator3 = devs.Model.create({
	rect: {x: 40, y: 1160, width: 130, height: 60},
	label: "Integrator3",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Integrator_111 = devs.Model.create({
	rect: {x: 550, y: 1320, width: 130, height: 60},
	label: "Integrator_111",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var WSum_111 = devs.Model.create({
	rect: {x: 740, y: 1320, width: 100, height: 60},
	label: "WSum_111",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1"],
	oPorts: ["out0"]
});
var NLFunction_8 = devs.Model.create({
	rect: {x: 820, y: 200, width: 130, height: 60},
	label: "NLFunction_8",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5","in6"],
	oPorts: ["out0"]
});
var NLFunction_12 = devs.Model.create({
	rect: {x: 230, y: 680, width: 130, height: 60},
	label: "NLFunction_12",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0","in1","in2","in3","in4","in5","in6","in7"],
	oPorts: ["out0"]
});
var LPF_1 = devs.Model.create({
	rect: {x: 1140, y: 1000, width: 100, height: 60},
	label: "LPF_1",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Integrator_232 = devs.Model.create({
	rect: {x: 40, y: 360, width: 130, height: 60},
	label: "Integrator_232",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});
var Mecanical_couple = devs.Model.create({
	rect: {x: 200, y: 200, width: 170, height: 60},
	label: "Mecanical_couple",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "orange" },
	shadow: true,
	iPorts: ["in0","in1"],
	oPorts: ["out0","out1"]
});
var Integrator_5678 = devs.Model.create({
	rect: {x: 1060, y: 360, width: 170, height: 60},
	label: "Integrator_5678",
	labelAttrs: { 'font-weight': 'bold', fill: 'white', 'font-size': '12px' },
	attrs: { fill: "blue" },
	shadow: true,
	iPorts: ["in0"],
	oPorts: ["out0"]
});


Electric_couple.addInner(NLFunction_8);
Mecanical_couple.addInner(Integrator_232);
Mecanical_couple.addInner(P);
Mecanical_couple.addInner(Integrator_23);
Mecanical_couple.addInner(WSum_23);
LPF3.addInner(WSum_56787);
LPF3.addInner(Integrator_5678);
LPF2.addInner(WSum_1234);
LPF2.addInner(Integrator_1234);
LPF1.addInner(WSum_2345);
LPF1.addInner(Integrator_2345);
FEM_R.addInner(NLFunction_6);
FEM_R.addInner(NLFunction_5);
FEM_R.addInner(NLFunction_3);
FEM_S.addInner(NLFunction_13);
FEM_S.addInner(NLFunction_12);
FEM_S.addInner(NLFunction_11);
Rotor.addInner(LPF_11);
Rotor.addInner(LPF_12);
Rotor.addInner(LPF_13);
Rotor.addInner(WSum_11);
Rotor.addInner(WSum_13);
Rotor.addInner(WSum_12);
Rotor.addInner(Integrator_13);
Rotor.addInner(Integrator_11);
Rotor.addInner(Integrator_12);
LPF_11.addInner(WSum_1111);
LPF_11.addInner(Integrator_1111);
LPF_12.addInner(WSum_2222);
LPF_12.addInner(Integrator_2222);
LPF_13.addInner(WSum_3333);
LPF_13.addInner(Integrator_3333);
Stator.addInner(Integrator3);
Stator.addInner(Integrator2);
Stator.addInner(LPF_3);
Stator.addInner(LPF_2);
Stator.addInner(LPF_1);
Stator.addInner(Integrator1);
Stator.addInner(WSum3);
Stator.addInner(WSum2);
Stator.addInner(WSum1);
LPF_3.addInner(WSum_333);
LPF_3.addInner(Integrator_333);
LPF_2.addInner(WSum_222);
LPF_2.addInner(Integrator_222);
LPF_1.addInner(WSum_111);
LPF_1.addInner(Integrator_111);

var arrow = devs.arrow;

Stator.port("o", "out2").joint(QuickScope.port("i", "in2"), arrow);
Stator.port("o", "out1").joint(QuickScope.port("i", "in1"), arrow);
Stator.port("o", "out0").joint(QuickScope.port("i", "in0"), arrow);
Rotor.port("o", "out2").joint(Electric_couple.port("i", "in5"), arrow);
Rotor.port("o", "out1").joint(Electric_couple.port("i", "in4"), arrow);
Rotor.port("o", "out0").joint(Electric_couple.port("i", "in3"), arrow);
Stator.port("o", "out2").joint(Electric_couple.port("i", "in2"), arrow);
Stator.port("o", "out1").joint(Electric_couple.port("i", "in1"), arrow);
Stator.port("o", "out0").joint(Electric_couple.port("i", "in0"), arrow);
FEM_R.port("o", "out2").joint(Rotor.port("i", "in5"), arrow);
FEM_R.port("o", "out1").joint(Rotor.port("i", "in4"), arrow);
FEM_R.port("o", "out0").joint(Rotor.port("i", "in3"), arrow);
SinGen3.port("o", "out0").joint(Stator.port("i", "in2"), arrow);
SinGen2.port("o", "out0").joint(Stator.port("i", "in1"), arrow);
SinGen1.port("o", "out0").joint(Stator.port("i", "in0"), arrow);
ConstGen3.port("o", "out0").joint(Rotor.port("i", "in2"), arrow);
ConstGen2.port("o", "out0").joint(Rotor.port("i", "in1"), arrow);
ConstGen1.port("o", "out0").joint(Rotor.port("i", "in0"), arrow);
Mecanical_couple.port("o", "out1").joint(FEM_R.port("i", "in6"), arrow);
Mecanical_couple.port("o", "out1").joint(FEM_S.port("i", "in6"), arrow);
Mecanical_couple.port("o", "out0").joint(FEM_R.port("i", "in7"), arrow);
Mecanical_couple.port("o", "out0").joint(FEM_S.port("i", "in7"), arrow);
Tl.port("o", "out0").joint(Mecanical_couple.port("i", "in1"), arrow);
Electric_couple.port("o", "out0").joint(Mecanical_couple.port("i", "in0"), arrow);
Mecanical_couple.port("o", "out1").joint(Electric_couple.port("i", "in6"), arrow);
NLFunction_8.port("o", "out0").joint(Electric_couple.port("o", "out0"), arrow);
Electric_couple.port("i", "in6").joint(NLFunction_8.port("i", "in6"), arrow);
Electric_couple.port("i", "in5").joint(NLFunction_8.port("i", "in5"), arrow);
Electric_couple.port("i", "in4").joint(NLFunction_8.port("i", "in4"), arrow);
Electric_couple.port("i", "in3").joint(NLFunction_8.port("i", "in3"), arrow);
Electric_couple.port("i", "in2").joint(NLFunction_8.port("i", "in2"), arrow);
Electric_couple.port("i", "in1").joint(NLFunction_8.port("i", "in1"), arrow);
Electric_couple.port("i", "in0").joint(NLFunction_8.port("i", "in0"), arrow);
Mecanical_couple.port("i", "in1").joint(WSum_23.port("i", "in1"), arrow);
P.port("o", "out0").joint(Integrator_232.port("i", "in0"), arrow);
Integrator_232.port("o", "out0").joint(Mecanical_couple.port("o", "out1"), arrow);
P.port("o", "out0").joint(Mecanical_couple.port("o", "out0"), arrow);
Integrator_23.port("o", "out0").joint(P.port("i", "in0"), arrow);
Integrator_23.port("o", "out0").joint(WSum_23.port("i", "in2"), arrow);
WSum_23.port("o", "out0").joint(Integrator_23.port("i", "in0"), arrow);
Mecanical_couple.port("i", "in0").joint(WSum_23.port("i", "in0"), arrow);
Rotor.port("o", "out5").joint(FEM_S.port("i", "in5"), arrow);
Rotor.port("o", "out4").joint(FEM_S.port("i", "in4"), arrow);
Rotor.port("o", "out3").joint(FEM_S.port("i", "in3"), arrow);
Rotor.port("o", "out2").joint(FEM_S.port("i", "in2"), arrow);
Rotor.port("o", "out1").joint(FEM_S.port("i", "in1"), arrow);
Rotor.port("o", "out0").joint(FEM_S.port("i", "in0"), arrow);
Stator.port("o", "out5").joint(FEM_R.port("i", "in5"), arrow);
Stator.port("o", "out4").joint(FEM_R.port("i", "in4"), arrow);
Stator.port("o", "out2").joint(FEM_R.port("i", "in2"), arrow);
Stator.port("o", "out3").joint(FEM_R.port("i", "in3"), arrow);
Stator.port("o", "out1").joint(FEM_R.port("i", "in1"), arrow);
Stator.port("o", "out0").joint(FEM_R.port("i", "in0"), arrow);
LPF3.port("o", "out0").joint(Stator.port("i", "in5"), arrow);
LPF2.port("o", "out0").joint(Stator.port("i", "in4"), arrow);
LPF1.port("o", "out0").joint(Stator.port("i", "in3"), arrow);
FEM_S.port("o", "out2").joint(LPF3.port("i", "in0"), arrow);
FEM_S.port("o", "out1").joint(LPF2.port("i", "in0"), arrow);
FEM_S.port("o", "out0").joint(LPF1.port("i", "in0"), arrow);
Integrator_5678.port("o", "out0").joint(WSum_56787.port("i", "in1"), arrow);
Integrator_5678.port("o", "out0").joint(LPF3.port("o", "out0"), arrow);
WSum_56787.port("o", "out0").joint(Integrator_5678.port("i", "in0"), arrow);
LPF3.port("i", "in0").joint(WSum_56787.port("i", "in0"), arrow);
Integrator_1234.port("o", "out0").joint(WSum_1234.port("i", "in1"), arrow);
Integrator_1234.port("o", "out0").joint(LPF2.port("o", "out0"), arrow);
WSum_1234.port("o", "out0").joint(Integrator_1234.port("i", "in0"), arrow);
LPF2.port("i", "in0").joint(WSum_1234.port("i", "in0"), arrow);
Integrator_2345.port("o", "out0").joint(WSum_2345.port("i", "in1"), arrow);
Integrator_2345.port("o", "out0").joint(LPF1.port("o", "out0"), arrow);
WSum_2345.port("o", "out0").joint(Integrator_2345.port("i", "in0"), arrow);
LPF1.port("i", "in0").joint(WSum_2345.port("i", "in0"), arrow);
NLFunction_6.port("o", "out0").joint(FEM_R.port("o", "out2"), arrow);
NLFunction_5.port("o", "out0").joint(FEM_R.port("o", "out1"), arrow);
NLFunction_3.port("o", "out0").joint(FEM_R.port("o", "out0"), arrow);
FEM_R.port("i", "in7").joint(NLFunction_3.port("i", "in7"), arrow);
FEM_R.port("i", "in7").joint(NLFunction_5.port("i", "in7"), arrow);
FEM_R.port("i", "in7").joint(NLFunction_6.port("i", "in7"), arrow);
FEM_R.port("i", "in6").joint(NLFunction_3.port("i", "in6"), arrow);
FEM_R.port("i", "in6").joint(NLFunction_5.port("i", "in6"), arrow);
FEM_R.port("i", "in6").joint(NLFunction_6.port("i", "in6"), arrow);
FEM_R.port("i", "in5").joint(NLFunction_6.port("i", "in5"), arrow);
FEM_R.port("i", "in5").joint(NLFunction_5.port("i", "in5"), arrow);
FEM_R.port("i", "in5").joint(NLFunction_3.port("i", "in5"), arrow);
FEM_R.port("i", "in4").joint(NLFunction_6.port("i", "in4"), arrow);
FEM_R.port("i", "in4").joint(NLFunction_3.port("i", "in4"), arrow);
FEM_R.port("i", "in3").joint(NLFunction_6.port("i", "in3"), arrow);
FEM_R.port("i", "in4").joint(NLFunction_5.port("i", "in4"), arrow);
FEM_R.port("i", "in3").joint(NLFunction_5.port("i", "in3"), arrow);
FEM_R.port("i", "in3").joint(NLFunction_3.port("i", "in3"), arrow);
FEM_R.port("i", "in2").joint(NLFunction_6.port("i", "in2"), arrow);
FEM_R.port("i", "in2").joint(NLFunction_5.port("i", "in2"), arrow);
FEM_R.port("i", "in2").joint(NLFunction_3.port("i", "in2"), arrow);
FEM_R.port("i", "in1").joint(NLFunction_6.port("i", "in1"), arrow);
FEM_R.port("i", "in1").joint(NLFunction_5.port("i", "in1"), arrow);
FEM_R.port("i", "in1").joint(NLFunction_3.port("i", "in1"), arrow);
FEM_R.port("i", "in0").joint(NLFunction_5.port("i", "in0"), arrow);
FEM_R.port("i", "in0").joint(NLFunction_6.port("i", "in0"), arrow);
FEM_R.port("i", "in0").joint(NLFunction_3.port("i", "in0"), arrow);
NLFunction_13.port("o", "out0").joint(FEM_S.port("o", "out2"), arrow);
NLFunction_12.port("o", "out0").joint(FEM_S.port("o", "out1"), arrow);
NLFunction_11.port("o", "out0").joint(FEM_S.port("o", "out0"), arrow);
FEM_S.port("i", "in7").joint(NLFunction_13.port("i", "in7"), arrow);
FEM_S.port("i", "in7").joint(NLFunction_12.port("i", "in7"), arrow);
FEM_S.port("i", "in7").joint(NLFunction_11.port("i", "in7"), arrow);
FEM_S.port("i", "in6").joint(NLFunction_13.port("i", "in6"), arrow);
FEM_S.port("i", "in6").joint(NLFunction_12.port("i", "in6"), arrow);
FEM_S.port("i", "in6").joint(NLFunction_11.port("i", "in6"), arrow);
FEM_S.port("i", "in5").joint(NLFunction_13.port("i", "in5"), arrow);
FEM_S.port("i", "in5").joint(NLFunction_12.port("i", "in5"), arrow);
FEM_S.port("i", "in5").joint(NLFunction_11.port("i", "in5"), arrow);
FEM_S.port("i", "in4").joint(NLFunction_13.port("i", "in4"), arrow);
FEM_S.port("i", "in4").joint(NLFunction_12.port("i", "in4"), arrow);
FEM_S.port("i", "in4").joint(NLFunction_11.port("i", "in4"), arrow);
FEM_S.port("i", "in3").joint(NLFunction_13.port("i", "in3"), arrow);
FEM_S.port("i", "in3").joint(NLFunction_12.port("i", "in3"), arrow);
FEM_S.port("i", "in3").joint(NLFunction_11.port("i", "in3"), arrow);
FEM_S.port("i", "in2").joint(NLFunction_13.port("i", "in2"), arrow);
FEM_S.port("i", "in2").joint(NLFunction_12.port("i", "in2"), arrow);
FEM_S.port("i", "in2").joint(NLFunction_11.port("i", "in2"), arrow);
FEM_S.port("i", "in1").joint(NLFunction_13.port("i", "in1"), arrow);
FEM_S.port("i", "in1").joint(NLFunction_12.port("i", "in1"), arrow);
FEM_S.port("i", "in1").joint(NLFunction_11.port("i", "in1"), arrow);
FEM_S.port("i", "in0").joint(NLFunction_13.port("i", "in0"), arrow);
FEM_S.port("i", "in0").joint(NLFunction_12.port("i", "in0"), arrow);
FEM_S.port("i", "in0").joint(NLFunction_11.port("i", "in0"), arrow);
LPF_12.port("o", "out0").joint(WSum_11.port("i", "in2"), arrow);
LPF_13.port("o", "out0").joint(WSum_11.port("i", "in3"), arrow);
LPF_13.port("o", "out0").joint(WSum_12.port("i", "in2"), arrow);
LPF_12.port("o", "out0").joint(WSum_13.port("i", "in2"), arrow);
LPF_11.port("o", "out0").joint(WSum_13.port("i", "in3"), arrow);
LPF_11.port("o", "out0").joint(WSum_12.port("i", "in3"), arrow);
Integrator_11.port("o", "out0").joint(WSum_11.port("i", "in0"), arrow);
Rotor.port("i", "in4").joint(WSum_12.port("i", "in4"), arrow);
Rotor.port("i", "in5").joint(WSum_13.port("i", "in4"), arrow);
Rotor.port("i", "in2").joint(WSum_13.port("i", "in1"), arrow);
Rotor.port("i", "in1").joint(WSum_12.port("i", "in1"), arrow);
Integrator_12.port("o", "out0").joint(WSum_12.port("i", "in0"), arrow);
Integrator_13.port("o", "out0").joint(WSum_13.port("i", "in0"), arrow);
Integrator_13.port("o", "out0").joint(Rotor.port("o", "out2"), arrow);
WSum_13.port("o", "out0").joint(Rotor.port("o", "out5"), arrow);
WSum_13.port("o", "out0").joint(LPF_13.port("i", "in0"), arrow);
WSum_13.port("o", "out0").joint(Integrator_13.port("i", "in0"), arrow);
WSum_12.port("o", "out0").joint(Rotor.port("o", "out4"), arrow);
WSum_12.port("o", "out0").joint(LPF_12.port("i", "in0"), arrow);
WSum_12.port("o", "out0").joint(Integrator_12.port("i", "in0"), arrow);
Integrator_12.port("o", "out0").joint(Rotor.port("o", "out1"), arrow);
Integrator_11.port("o", "out0").joint(Rotor.port("o", "out0"), arrow);
WSum_11.port("o", "out0").joint(Rotor.port("o", "out3"), arrow);
WSum_11.port("o", "out0").joint(LPF_11.port("i", "in0"), arrow);
WSum_11.port("o", "out0").joint(Integrator_11.port("i", "in0"), arrow);
Rotor.port("i", "in3").joint(WSum_11.port("i", "in4"), arrow);
Rotor.port("i", "in0").joint(WSum_11.port("i", "in1"), arrow);
Integrator_1111.port("o", "out0").joint(WSum_1111.port("i", "in1"), arrow);
Integrator_1111.port("o", "out0").joint(LPF_11.port("o", "out0"), arrow);
WSum_1111.port("o", "out0").joint(Integrator_1111.port("i", "in0"), arrow);
LPF_11.port("i", "in0").joint(WSum_1111.port("i", "in0"), arrow);
Integrator_2222.port("o", "out0").joint(WSum_2222.port("i", "in1"), arrow);
Integrator_2222.port("o", "out0").joint(LPF_12.port("o", "out0"), arrow);
WSum_2222.port("o", "out0").joint(Integrator_2222.port("i", "in0"), arrow);
LPF_12.port("i", "in0").joint(WSum_2222.port("i", "in0"), arrow);
Integrator_3333.port("o", "out0").joint(WSum_3333.port("i", "in1"), arrow);
Integrator_3333.port("o", "out0").joint(LPF_13.port("o", "out0"), arrow);
WSum_3333.port("o", "out0").joint(Integrator_3333.port("i", "in0"), arrow);
LPF_13.port("i", "in0").joint(WSum_3333.port("i", "in0"), arrow);
LPF_2.port("o", "out0").joint(WSum3.port("i", "in2"), arrow);
LPF_2.port("o", "out0").joint(WSum1.port("i", "in2"), arrow);
LPF_3.port("o", "out0").joint(WSum1.port("i", "in3"), arrow);
LPF_1.port("o", "out0").joint(WSum3.port("i", "in3"), arrow);
LPF_1.port("o", "out0").joint(WSum2.port("i", "in2"), arrow);
LPF_3.port("o", "out0").joint(WSum2.port("i", "in3"), arrow);
Integrator3.port("o", "out0").joint(WSum3.port("i", "in0"), arrow);
Stator.port("i", "in5").joint(WSum3.port("i", "in4"), arrow);
Stator.port("i", "in2").joint(WSum3.port("i", "in1"), arrow);
WSum3.port("o", "out0").joint(LPF_3.port("i", "in0"), arrow);
WSum3.port("o", "out0").joint(Stator.port("o", "out5"), arrow);
Integrator3.port("o", "out0").joint(Stator.port("o", "out2"), arrow);
WSum3.port("o", "out0").joint(Integrator3.port("i", "in0"), arrow);
Stator.port("i", "in4").joint(WSum2.port("i", "in4"), arrow);
Stator.port("i", "in1").joint(WSum2.port("i", "in1"), arrow);
Integrator2.port("o", "out0").joint(WSum2.port("i", "in0"), arrow);
WSum2.port("o", "out0").joint(Stator.port("o", "out4"), arrow);
WSum2.port("o", "out0").joint(LPF_2.port("i", "in0"), arrow);
Integrator2.port("o", "out0").joint(Stator.port("o", "out1"), arrow);
Integrator1.port("o", "out0").joint(WSum1.port("i", "in0"), arrow);
WSum2.port("o", "out0").joint(Integrator2.port("i", "in0"), arrow);
WSum1.port("o", "out0").joint(LPF_1.port("i", "in0"), arrow);
Integrator_333.port("o", "out0").joint(WSum_333.port("i", "in1"), arrow);
Integrator_333.port("o", "out0").joint(LPF_3.port("o", "out0"), arrow);
WSum_333.port("o", "out0").joint(Integrator_333.port("i", "in0"), arrow);
LPF_3.port("i", "in0").joint(WSum_333.port("i", "in0"), arrow);
Integrator_222.port("o", "out0").joint(WSum_222.port("i", "in1"), arrow);
Integrator_222.port("o", "out0").joint(LPF_2.port("o", "out0"), arrow);
WSum_222.port("o", "out0").joint(Integrator_222.port("i", "in0"), arrow);
LPF_2.port("i", "in0").joint(WSum_222.port("i", "in0"), arrow);
Integrator_111.port("o", "out0").joint(WSum_111.port("i", "in1"), arrow);
Integrator_111.port("o", "out0").joint(LPF_1.port("o", "out0"), arrow);
WSum_111.port("o", "out0").joint(Integrator_111.port("i", "in0"), arrow);
LPF_1.port("i", "in0").joint(WSum_111.port("i", "in0"), arrow);
Integrator1.port("o", "out0").joint(Stator.port("o", "out0"), arrow);
WSum1.port("o", "out0").joint(Integrator1.port("i", "in0"), arrow);
WSum1.port("o", "out0").joint(Stator.port("o", "out3"), arrow);
Stator.port("i", "in3").joint(WSum1.port("i", "in4"), arrow);
Stator.port("i", "in0").joint(WSum1.port("i", "in1"), arrow);
