import Header from "../components/Header";
import Footer from "../components/Footer";
import ChatContainer from "../components/ChatContainer";

export default function Page() {
  return (
    <>
      <Header />
      <main
        style={{
          marginTop: "var(--header-height)",
          minHeight: `calc(100vh - var(--header-height))`,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <ChatContainer />
    </main>
      <Footer />
    </>
  );
}



