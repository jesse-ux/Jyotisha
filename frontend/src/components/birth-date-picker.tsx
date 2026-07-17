"use client";

import { format } from "date-fns";
import { zhCN } from "date-fns/locale";
import { CalendarIcon } from "lucide-react";
import { useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { formatBirthDate, parseBirthDate } from "@/lib/birth-time-intake-model";

type BirthDatePickerProps = {
  readonly value: string;
  readonly disabled: boolean;
  readonly onChange: (value: string) => void;
};

export function BirthDatePicker({ value, disabled, onChange }: BirthDatePickerProps) {
  const labelId = useId();
  const valueId = useId();
  const [open, setOpen] = useState(false);
  const selected = parseBirthDate(value);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return (
    <div className="grid gap-2">
      <span id={labelId}>出生日期</span>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger
          render={<Button
            type="button"
            variant="outline"
            disabled={disabled}
            aria-labelledby={`${labelId} ${valueId}`}
            data-empty={selected === undefined}
            className="w-full justify-start px-3 text-left font-normal data-[empty=true]:text-muted-foreground"
          />}
        >
          <CalendarIcon aria-hidden="true" />
          <span id={valueId}>
            {selected === undefined
              ? "选择出生日期"
              : format(selected, "PPP", { locale: zhCN })}
          </span>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-auto p-0">
          <Calendar
            key={value || "empty"}
            mode="single"
            className="[--cell-size:2.75rem] [&_button[data-selected-single=true]]:text-primary-foreground!"
            locale={zhCN}
            selected={selected}
            defaultMonth={selected ?? today}
            captionLayout="dropdown"
            navLayout="after"
            startMonth={new Date(1900, 0)}
            endMonth={today}
            reverseYears
            disabled={{ before: new Date(1900, 0, 1), after: today }}
            onSelect={(nextDate) => {
              if (nextDate === undefined) return;
              onChange(formatBirthDate(nextDate));
              setOpen(false);
            }}
          />
        </PopoverContent>
      </Popover>
    </div>
  );
}
