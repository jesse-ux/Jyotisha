"use client";

import type { JourneyClientResponse } from "@/lib/birth-time-journey-client";
import type { BirthTimeGuidedController } from "@/hooks/use-birth-time-guided-journey";
import { guidedTerminalPath } from "@/lib/birth-time-guided-terminal";

type CandidateResultProps = {
  readonly journey: JourneyClientResponse;
  readonly controller: BirthTimeGuidedController;
};

const confidenceLabels = {
  low: "证据不足",
  medium: "中等置信",
  high: "较高置信",
} as const;

export function BirthTimeCandidateResult({ journey, controller }: CandidateResultProps) {
  const result = journey.candidateResult;
  const action = journey.nextAction;
  const dynamic = journey.journeyProtocol === "dynamic-choice-v2";
  const terminalPath = guidedTerminalPath(journey);
  if (result?.eventCount === 0) {
    return (
      <div className="birth-time-candidate-result" aria-live="polite">
        <p className="birth-time-assessment-unavailable">尚未进入分钟计算：还没有可评分的关键经历资料。</p>
        <p className="birth-time-evidence-boundary">当前范围仅为填报范围，不是校正结果；请补充跨领域、可注明年月的重大事件后重新评估。</p>
        {terminalPath && <button className="button-secondary birth-time-guided-action" disabled={controller.pending} type="button" onClick={controller.editBirthTimeDetails}>补充资料并重新评估</button>}
      </div>
    );
  }
  if (!result && action.kind === "present_low_result") {
    return (
      <div className="birth-time-candidate-result" aria-live="polite">
        <p className="birth-time-evidence-boundary">系统不会选择或应用未经证据支持的具体分钟，<span className="phrase-nowrap">当前排盘使用时间</span>保持不变。</p>
        {terminalPath && <TerminalAction controller={controller} path={terminalPath} />}
      </div>
    );
  }
  if (!result) return null;
  const winner = result.winningSegment;
  const receipt = result.techniqueReceipt;

  return (
    <div className="birth-time-candidate-result" aria-live="polite">
      <div className="birth-time-candidate-heading">
        <b>{dynamic ? "候选范围评估结果" : "关键经历评分结果"}</b>
        <span>{confidenceLabels[result.confidence]}</span>
      </div>
      {winner ? (
        <dl className="birth-time-candidate-grid">
          <div><dt>候选时间范围</dt><dd>{winner.startTime}—{winner.endTime}</dd></div>
          <div><dt>候选代表时间</dt><dd>{winner.representativeTime}</dd></div>
          {!dynamic && <div><dt>有效经历</dt><dd>{result.eventCount} 条 / {result.domainCount} 个领域</dd></div>}
          {!dynamic && <div><dt>领先幅度</dt><dd>{result.marginPercent}%</dd></div>}
        </dl>
      ) : (
        <p className="birth-time-assessment-unavailable">候选仍然并列或缺少必要计算层，系统不会选择具体分钟。</p>
      )}
      <p className="birth-time-evidence-boundary">这是可复现的候选评分，不代表已经证明出生记录中的具体分钟。</p>
      {receipt && (
        <details className="birth-time-evidence-receipt">
          <summary>本次计算回执</summary>
          <p>已用：{[...receipt.usedDivisionalCharts, ...receipt.usedArudha, ...receipt.dashaTracks].join("、") || "无"}</p>
          <p>辅助：{receipt.auxiliaryLayers.join("、") || "无"}</p>
          <p>未完成：{receipt.missingLayers.join("、") || "无"}</p>
          {receipt.hardBlockers.length > 0 && <p>阻止确认：{receipt.hardBlockers.join("、")}</p>}
        </details>
      )}

      {action.kind === "present_low_result" && (
        <div className="birth-time-candidate-terminal" role="status">
          <p>{dynamic ? "目前没有足够的新信息继续稳定缩小范围，本次评估已结束并保存当前候选范围。" : "本轮校正已安全结束，只保留候选范围，当前排盘使用时间保持不变。"}</p>
          {terminalPath && <TerminalAction controller={controller} path={terminalPath} />}
        </div>
      )}
      {action.kind === "present_medium_result" && winner && dynamic && (
        <div className="birth-time-candidate-terminal" role="status">
          <p>已形成较窄的候选范围，本次评估已结束；它不会自动改动<span className="phrase-nowrap">当前排盘使用时间</span>。</p>
          {terminalPath && <TerminalAction controller={controller} path={terminalPath} />}
        </div>
      )}
      {action.kind === "present_medium_result" && winner && !dynamic && (
        <div className="birth-time-candidate-terminal">
          <p>可以保存候选时间范围，代表时间不会<span className="phrase-nowrap">用于</span>排盘。</p>
          <button className="button-primary birth-time-guided-action" disabled={controller.pending} type="button" onClick={() => controller.saveCandidate(result.resultId)}>
            {controller.pending ? "保存中…" : "保存候选范围"}
          </button>
        </div>
      )}
      {action.kind === "candidate_saved" && (
        <div className="birth-time-candidate-terminal" role="status">
          <p className="birth-time-success-note">候选时间范围已保存。<span className="phrase-nowrap">当前排盘使用时间</span>没有改变。</p>
          {terminalPath && <TerminalAction controller={controller} path={terminalPath} />}
        </div>
      )}
      {action.kind === "request_candidate_confirmation" && winner && (
        <div className="birth-time-confirmation-panel">
          <b>确认<span className="phrase-nowrap">当前排盘使用时间</span></b>
          <p><span className="phrase-nowrap">候选时间</span>为 {winner.representativeTime}。确认后它会成为<span className="phrase-nowrap">当前排盘使用时间</span>，<span className="phrase-nowrap">原始填报时间</span>仍会保留。</p>
          <button className="button-primary birth-time-guided-action" disabled={controller.pending} type="button" onClick={() => controller.confirmCandidate(result.resultId, winner.representativeTime)}>
            {controller.pending ? "确认中…" : `确认使用 ${winner.representativeTime}`}
          </button>
        </div>
      )}
      {action.kind === "ready" && (
        <div className="birth-time-candidate-terminal" role="status">
          <p className="birth-time-success-note"><span className="phrase-nowrap">当前排盘使用时间</span>已更新为 {action.activeTime}，<span className="phrase-nowrap">原始填报时间</span>仍已保留。</p>
          <button className="button-primary birth-time-guided-action" disabled={controller.pending} type="button" onClick={controller.acknowledgeReady}>继续使用此排盘</button>
        </div>
      )}
    </div>
  );
}

function TerminalAction({ controller, path }: {
  readonly controller: BirthTimeGuidedController;
  readonly path: NonNullable<ReturnType<typeof guidedTerminalPath>>;
}) {
  if (path.kind === "complete_with_candidate") {
    return (
      <div className="birth-time-new-assessment">
        <button className="button-primary birth-time-guided-action" disabled={controller.pending} onClick={() => controller.completeCandidate(path.time)} type="button">
          {controller.pending ? "保存中…" : "完成并继续对话"}
        </button>
        <small>将以 {path.time} 作为当前工作排盘时间；候选状态和原始资料都会保留。</small>
      </div>
    );
  }
  return (
    <div className="birth-time-new-assessment">
      <button className="button-secondary birth-time-guided-action" disabled={controller.pending} onClick={controller.editBirthTimeDetails} type="button">开始新的评估</button>
      <small>会建立新的记录，当前结果仍会保留。</small>
    </div>
  );
}
