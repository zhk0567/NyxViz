import { convertZFastToVtk } from '../data/vtkLayout';

export interface VtkConvertRequest {
  id: number;
  buffer: ArrayBuffer;
}

export interface VtkConvertResponse {
  id: number;
  buffer: ArrayBuffer;
}

self.onmessage = (ev: MessageEvent<VtkConvertRequest>) => {
  const { id, buffer } = ev.data;
  const zFast = new Float32Array(buffer);
  const out = convertZFastToVtk(zFast);
  self.postMessage({ id, buffer: out.buffer } satisfies VtkConvertResponse, [
    out.buffer,
  ]);
};
