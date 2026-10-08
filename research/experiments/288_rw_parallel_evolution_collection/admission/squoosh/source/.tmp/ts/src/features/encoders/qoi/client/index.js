export function encode(signal, workerBridge, imageData, options) {
    return workerBridge.qoiEncode(signal, imageData, options);
}
