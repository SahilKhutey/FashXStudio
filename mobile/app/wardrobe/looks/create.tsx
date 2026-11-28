import React from "react";
import { useLocalSearchParams, router } from "expo-router";
import { CreateLookForm } from "../../../src/features/wardrobe/components/CreateLookForm";

export default function CreateLookRoute() {
  const { itemIds } = useLocalSearchParams<{ itemIds?: string }>();
  const selectedItemIds = itemIds
    ? itemIds.split(",").map((id) => id.trim()).filter(Boolean)
    : [];

  return (
    <CreateLookForm
      selectedItemIds={selectedItemIds}
      onCreated={() => {
        router.replace("/(tabs)/looks");
      }}
    />
  );
}
