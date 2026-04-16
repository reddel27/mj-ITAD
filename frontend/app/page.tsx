import DispensaryBrowser from '../components/DispensaryBrowser'

export default function Home() {
  return (
    <main className="min-h-screen p-4 md:p-6">
      <h1 className="text-3xl font-bold mb-2">MJ-ITAD</h1>
      <p className="mb-6 text-gray-700">Find marijuana prices at dispensaries near you</p>
      <DispensaryBrowser />
    </main>
  )
}