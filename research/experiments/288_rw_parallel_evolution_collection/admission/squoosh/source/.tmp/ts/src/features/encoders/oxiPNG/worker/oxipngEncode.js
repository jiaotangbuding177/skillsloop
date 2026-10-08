import checkThreadsSupport from 'worker-shared/supports-wasm-threads';
async function initMT() {
    const { default: init, initThreadPool, optimise, } = await import('codecs/oxipng/pkg-parallel/squoosh_oxipng');
    await init();
    await initThreadPool(navigator.hardwareConcurrency);
    return optimise;
}
async function initST() {
    const { default: init, optimise } = await import('codecs/oxipng/pkg/squoosh_oxipng');
    await init();
    return optimise;
}
let wasmReady;
export default async function encode(data, options) {
    if (!wasmReady) {
        wasmReady = checkThreadsSupport().then((hasThreads) => hasThreads ? initMT() : initST());
    }
    const optimise = await wasmReady;
    return optimise(data.data, data.width, data.height, options.level, options.interlace).buffer;
}
