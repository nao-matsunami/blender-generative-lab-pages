import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const preview = document.querySelector('#preview');
const start = document.querySelector('#start');
const status = document.querySelector('#status');
const hint = document.querySelector('#xr-hint');
const shadowSwitch = document.querySelector('#shadows');

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(38, 1, 0.01, 30);
camera.position.set(0.27, 0.30, 0.63);
camera.lookAt(0, 0.15, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.xr.enabled = true;
renderer.xr.setReferenceSpaceType('local');
preview.append(renderer.domElement);

function fitPreview() {
  if (renderer.xr.isPresenting) return;
  const { clientWidth: width, clientHeight: height } = preview;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height, false);
}
new ResizeObserver(fitPreview).observe(preview);
fitPreview();

const rig = new THREE.Group();
scene.add(rig);
scene.add(new THREE.HemisphereLight(0xfff4e2, 0xa2c6d2, 0.75));
const lamp = new THREE.DirectionalLight(0xfff5e5, 3.3);
lamp.position.set(-0.19, 0.42, 0.40);
lamp.target.position.set(0, 0.195, 0);
lamp.castShadow = true;
lamp.shadow.mapSize.set(1024, 1024);
Object.assign(lamp.shadow.camera, {
  left: -0.18, right: 0.18, top: 0.18, bottom: -0.18, near: 0.05, far: 1.15
});
lamp.shadow.camera.updateProjectionMatrix();
lamp.shadow.normalBias = 0.00035;
rig.add(lamp, lamp.target);
shadowSwitch.addEventListener('change', () => {
  lamp.castShadow = shadowSwitch.checked;
});

const { scene: planet, animations } = await new GLTFLoader().loadAsync('../clockwork-planet/planet-ar.glb');
const casters = /^(Meridianbrass|Meridianenameledge|Innerorbitinlay|Obliqueinnerorbit|Satelliteorbit)$/i;
planet.traverse(mesh => {
  if (!mesh.isMesh) return;
  mesh.castShadow = casters.test(mesh.name.replace(/[^a-z]/gi, ''));
  if (/^oceanplanet$/i.test(mesh.name.replace(/[^a-z]/gi, ''))) {
    mesh.receiveShadow = true;
    mesh.material = mesh.material.clone();
    mesh.material.metalness = 0.25;
    mesh.material.roughness = 0.34;
  }
});
rig.add(planet);
const mixer = new THREE.AnimationMixer(planet);
mixer.clipAction(animations[0]).play();

const marker = new THREE.Mesh(
  new THREE.RingGeometry(0.043, 0.048, 48).rotateX(-Math.PI / 2),
  new THREE.MeshBasicMaterial({ color: 0xefd19e, side: THREE.DoubleSide })
);
marker.matrixAutoUpdate = false;
marker.visible = false;
scene.add(marker);

let source;
let placed = false;
let lastTime;
renderer.setAnimationLoop((time, frame) => {
  if (lastTime !== undefined) mixer.update(Math.min((time - lastTime) / 1000, 0.08));
  lastTime = time;
  if (frame && source && !placed) {
    const hit = frame.getHitTestResults(source)[0];
    const pose = hit?.getPose(renderer.xr.getReferenceSpace());
    marker.visible = Boolean(pose);
    if (pose) {
      marker.matrix.fromArray(pose.transform.matrix);
      marker.matrixWorldNeedsUpdate = true;
    }
  }
  renderer.render(scene, camera);
});

const canStart = await navigator.xr?.isSessionSupported('immersive-ar').catch(() => false);
status.textContent = canStart
  ? 'プレビューで影のオン・オフを比較できます。'
  : 'この端末では3Dプレビューを表示しています。ARはPixel 7のChromeで試せます。';
start.disabled = !canStart;

start.addEventListener('click', async () => {
  start.disabled = true;
  let session;
  try {
    session = await navigator.xr.requestSession('immersive-ar', {
      requiredFeatures: ['hit-test'],
      optionalFeatures: ['dom-overlay'],
      domOverlay: { root: hint }
    });
    session.addEventListener('end', () => {
      source?.cancel();
      source = undefined;
      placed = false;
      marker.visible = false;
      rig.visible = true;
      rig.position.set(0, 0, 0);
      hint.textContent = '机にカメラを向け、輪が出た場所をタップ';
      start.disabled = false;
      status.textContent = 'ARを終了しました。もう一度試せます。';
      requestAnimationFrame(fitPreview);
    }, { once: true });
    session.addEventListener('select', () => {
      if (!marker.visible || placed) return;
      rig.position.setFromMatrixPosition(marker.matrix);
      rig.visible = true;
      placed = true;
      marker.visible = false;
      hint.textContent = 'リングの影が惑星を横切ります';
    });
    rig.visible = false;
    await renderer.xr.setSession(session);
    const viewerSpace = await session.requestReferenceSpace('viewer');
    source = await session.requestHitTestSource({ space: viewerSpace });
  } catch (error) {
    if (session) await session.end().catch(() => {});
    rig.visible = true;
    start.disabled = false;
    status.textContent = 'ARを開始できませんでした。Chromeのカメラ権限とGoogle Play 開発者サービス（AR）を確認してください。';
    console.error(error);
  }
});
