import qoiDecoder from 'codecs/qoi/dec/qoi_dec';
import { initEmscriptenModule, blobToArrayBuffer } from 'features/worker-utils';
let emscriptenModule;
export default async function decode(blob) {
    if (!emscriptenModule) {
        emscriptenModule = initEmscriptenModule(qoiDecoder);
    }
    const [module, data] = await Promise.all([
        emscriptenModule,
        blobToArrayBuffer(blob),
    ]);
    const result = module.decode(data);
    if (!result)
        throw new Error('Decoding error');
    return result;
}
