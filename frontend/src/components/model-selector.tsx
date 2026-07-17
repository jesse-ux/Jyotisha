"use client";

import { Popover } from "@base-ui/react/popover";
import { Check, ChevronDown } from "lucide-react";
import { useId, useState } from "react";
import type { KeyboardEvent } from "react";
import type { PublicLanguageModel } from "@/lib/public-models";

type ModelSelectorProps = {
  readonly models: readonly PublicLanguageModel[];
  readonly selectedModelId: string;
  readonly disabled?: boolean;
  readonly onSelect: (modelId: string) => void;
};

export function ModelSelector({
  models,
  selectedModelId,
  disabled = false,
  onSelect,
}: ModelSelectorProps) {
  const [open, setOpen] = useState(false);
  const groupName = useId();
  const selectedModel = models.find((model) => model.id === selectedModelId);
  const unavailable = models.length === 0;

  function moveRadioSelection(event: KeyboardEvent<HTMLInputElement>, index: number) {
    const step = event.key === "ArrowDown" || event.key === "ArrowRight"
      ? 1
      : event.key === "ArrowUp" || event.key === "ArrowLeft"
        ? -1
        : 0;
    if (step === 0 || models.length < 2) return;

    event.preventDefault();
    const nextIndex = (index + step + models.length) % models.length;
    const nextModel = models[nextIndex];
    if (!nextModel) return;
    onSelect(nextModel.id);
    setOpen(false);
  }

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger
        className="model-selector-trigger"
        type="button"
        disabled={disabled || unavailable}
        aria-label={selectedModel ? `当前模型：${selectedModel.label}，点击切换` : "模型暂不可用"}
      >
        <span>模型</span>
        <b>{selectedModel?.label ?? "暂不可用"}</b>
        <ChevronDown aria-hidden="true" />
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Positioner className="model-selector-positioner" side="top" align="start" sideOffset={8} collisionPadding={12}>
          <Popover.Popup className="model-selector-popup">
            <Popover.Title className="model-selector-title">选择模型</Popover.Title>
            <Popover.Description className="model-selector-description">
              只影响之后发送的问题，每次消耗 1 点。
            </Popover.Description>
            <fieldset className="model-selector-options">
              <legend className="sr-only">选择当前对话使用的模型</legend>
              {models.map((model, index) => (
                <label className="model-selector-option" data-selected={model.id === selectedModelId ? "" : undefined} key={model.id}>
                  <input
                    className="sr-only"
                    type="radio"
                    name={groupName}
                    value={model.id}
                    checked={model.id === selectedModelId}
                    onChange={() => onSelect(model.id)}
                    onClick={() => {
                      if (model.id === selectedModelId) onSelect(model.id);
                      setOpen(false);
                    }}
                    onKeyDown={(event) => moveRadioSelection(event, index)}
                  />
                  <span className="model-selector-copy">
                    <b>{model.label}</b>
                    <small>{model.description || "通用分析模型"}</small>
                  </span>
                  <span className="model-selector-cost">{model.creditCost} 点/次</span>
                  <Check className="model-selector-check" aria-hidden="true" />
                </label>
              ))}
            </fieldset>
          </Popover.Popup>
        </Popover.Positioner>
      </Popover.Portal>
    </Popover.Root>
  );
}
