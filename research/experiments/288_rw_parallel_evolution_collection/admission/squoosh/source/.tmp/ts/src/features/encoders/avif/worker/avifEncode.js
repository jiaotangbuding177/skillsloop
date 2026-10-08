import { initEmscriptenModule } from 'features/worker-utils';
import checkThreadsSupport from 'worker-shared/supports-wasm-threads';
let emscriptenModule;
async function init() {
    if (await checkThreadsSupport()) {
        const avifEncoder = await import('codecs/avif/enc/avif_enc_mt');
        return initEmscriptenModule(avifEncoder.default);
    }
    const avifEncoder = await import('codecs/avif/enc/avif_enc.js');
    return initEmscriptenModule(avifEncoder.default);
}
export default async function encode(data, options) {
    if (!emscriptenModule)
        emscriptenModule = init();
    const module = await emscriptenModule;
    const result = module.encode(data.data, data.width, data.height, options);
    if (!result)
        throw new Error('Encoding error');
    return result.buffer;
}
