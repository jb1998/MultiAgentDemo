import { describe, expect, it } from 'vitest';
import { buildRoutingPreview, parseTaskLines } from './smartRouting';

describe('parseTaskLines', () => {
  it('splits on newlines and trims', () => {
    expect(parseTaskLines('  a  \n  b  ')).toEqual(['a', 'b']);
  });

  it('ignores empty lines', () => {
    expect(parseTaskLines('a\n\nb')).toEqual(['a', 'b']);
  });
});

describe('buildRoutingPreview', () => {
  it('suggests calculator for math line', () => {
    const plan = buildRoutingPreview('Calculate 10 + 5');
    expect(plan[0].suggestedTool).toBe('Calculator');
    expect(plan[0].intent).toBe('calculation');
  });

  it('suggests weather tool for forecast line', () => {
    const plan = buildRoutingPreview('What is the weather in Tokyo?');
    expect(plan[0].suggestedTool).toBe('WeatherMock');
  });

  it('builds multi-line preview', () => {
    const text = 'Calculate 1+1\nConvert hello to uppercase';
    const plan = buildRoutingPreview(text);
    expect(plan.length).toBe(2);
    expect(plan.map((p) => p.suggestedTool)).toContain('Calculator');
    expect(plan.map((p) => p.suggestedTool)).toContain('TextProcessor');
  });
});
