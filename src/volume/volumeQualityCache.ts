/** 会话级：某时间步已完成 presentation 质量体渲染 */
const presentationReady = new Set<number>();

export function markPresentationReady(timestep: number): void {
  presentationReady.add(timestep);
}

export function isPresentationReady(timestep: number): boolean {
  return presentationReady.has(timestep);
}

export function clearPresentationCache(): void {
  presentationReady.clear();
}
