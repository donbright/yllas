// Mars


var clock = new THREE.Clock();

camera = new THREE.PerspectiveCamera( 60, window.innerWidth / window.innerHeight, 1, 10000 );

controls = new THREE.FirstPersonControls( camera );
controls.movementSpeed = 20;
controls.lookSpeed = 0.05;

var scene = new THREE.Scene();

var renderer = new THREE.WebGLRenderer();
//var renderer = new THREE.CanvasRenderer();
renderer.setSize( window.innerWidth, window.innerHeight );
document.body.appendChild( renderer.domElement );

ambientLight = new THREE.AmbientLight( 0xcccccc );
scene.add( ambientLight );
dirLight = new THREE.DirectionalLight( 0xabffe4, 1.0 );
dirLight.position.set( 5, 5, 10 );
scene.add( dirLight );


// Astronaut / Cosmonaut
var boxgeometry = new THREE.BoxGeometry( 1, 3, 1 );
var boxmaterial = new THREE.MeshLambertMaterial(  { color: 0xaadddd, specular: 0x009900, shininess: 30, shading: THREE.FlatShading } );
var cube = new THREE.Mesh( boxgeometry, boxmaterial );
scene.add( cube );

// Land
var texture = new THREE.TextureLoader().load( "red1.png" );
// 127 tiles = 128 vertexes
var pw = 128, ph = 128, cw = 127, ch = 127;
var planegeometry = new THREE.PlaneGeometry( pw, ph, cw, ch );
//l = planegeometry.vertices.length;
for ( var i = 0 ; i <= cw ; i ++ ) {
	for ( var j = 0 ; j <= ch ; j ++ ) {
		planegeometry.vertices[ i*(ch+1) + j ].z = Math.sin((i*i+j*j)/(10*100));
	}
}
planegeometry.vertices[0].z = -1 ;
var planematerial = new THREE.MeshLambertMaterial( { color: 0x992222, map:texture } );
//var planematerial = new THREE.MeshLambertMaterial( {wireframe: true} );
//var planematerial = new THREE.MeshPhongMaterial( { color: 0x992222, specular: 0x000000, shininess: 3, shading: THREE.FlatShading } );
var plane = new THREE.Mesh( planegeometry, planematerial );
plane.rotation.x = -3.14/2;
scene.add( plane );



camera.position.z = 6;
camera.position.y = 2;


var render = function () {

	requestAnimationFrame( render );

	cube.rotation.y += 0.01;

	controls.update( clock.getDelta() );
	renderer.render(scene, camera);
};

render();
