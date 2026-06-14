export type TaskMode = 'auto' | 'single' | 'smart_multi';

export interface RoutingPreviewLine {
  index: number;
  text: string;
  intent: string;
  suggestedTool: string;
}

function detectIntent(line: string): string {
  const lowered = line.toLowerCase();
  if (/\d+\s*[\+\-\*/\^%x]\s*\d+/.test(lowered) || /calculate|compute|sqrt/.test(lowered)) {
    return 'calculation';
  }
  if (/uppercase|lowercase|reverse|word count|remove space/.test(lowered)) {
    return 'text_processing';
  }
  if (/weather|forecast/.test(lowered)) {
    return 'weather';
  }
  if (/time|date|today/.test(lowered)) {
    return 'datetime';
  }
  if (/json|\{.*\}|\[.*\]/.test(lowered)) {
    return 'json';
  }
  if (/convert/.test(lowered) && /\d+\s*(km|m|mi|kg|lb|c|f)/.test(lowered)) {
    return 'unit_conversion';
  }
  return 'general';
}

function suggestTool(line: string, intent: string): string {
  const lowered = line.toLowerCase();
  switch (intent) {
    case 'calculation':
      return 'Calculator';
    case 'text_processing':
      return 'TextProcessor';
    case 'weather':
      return 'WeatherMock';
    case 'datetime':
      return 'DateTimeTool';
    case 'json':
      return 'JSONProcessorTool';
    case 'unit_conversion':
      return 'UnitConverterTool';
    default:
      if (/weather/.test(lowered)) return 'WeatherMock';
      if (/calculate|compute|\d+\s*[\+\-\*/]/.test(lowered)) return 'Calculator';
      return 'TextProcessor';
  }
}

export function parseTaskLines(text: string): string[] {
  return text
    .replace(/\r\n/g, '\n')
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);
}

export function buildRoutingPreview(text: string): RoutingPreviewLine[] {
  return parseTaskLines(text).map((line, i) => {
    const intent = detectIntent(line);
    return {
      index: i + 1,
      text: line,
      intent,
      suggestedTool: suggestTool(line, intent),
    };
  });
}
