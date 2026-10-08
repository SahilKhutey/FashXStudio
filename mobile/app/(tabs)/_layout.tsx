import { Tabs } from "expo-router";
import React from "react";

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        tabBarActiveTintColor: "#38BDF8",
        tabBarInactiveTintColor: "#94A3B8",
        tabBarStyle: {
          backgroundColor: "#0F172A",
          borderTopColor: "#1E293B",
        },
        headerStyle: {
          backgroundColor: "#0F172A",
        },
        headerTitleStyle: {
          color: "#F8FAFC",
          fontWeight: "700",
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Feed",
          headerTitle: "FashXStudio",
        }}
      />
      <Tabs.Screen
        name="tryon"
        options={{
          title: "Try-On",
          headerTitle: "Virtual Fitting Room",
        }}
      />
      <Tabs.Screen
        name="closet"
        options={{
          title: "Closet",
          headerTitle: "My Wardrobe",
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: "Profile",
          headerTitle: "Fashion Identity",
        }}
      />
    </Tabs>
  );
}
