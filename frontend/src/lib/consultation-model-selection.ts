export async function reserveConsultationModel<
  Model extends { readonly id: string },
  Reservation,
>(
  modelId: string,
  resolveModel: (modelId: string) => Model | null,
  reserveCredit: () => Promise<Reservation>,
) {
  const model = resolveModel(modelId);
  if (!model) return { status: "unavailable" } as const;

  return {
    status: "reserved",
    model,
    usageModelId: model.id,
    reservation: await reserveCredit(),
  } as const;
}
