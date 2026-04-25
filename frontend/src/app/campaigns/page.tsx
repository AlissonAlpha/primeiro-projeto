import { TrendingUp, Plus, Circle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function CampaignsPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Campanhas</h1>
          <p className="text-muted-foreground text-sm mt-1">Gerencie todas as campanhas ativas</p>
        </div>
        <Link href="/agents/traffic-manager">
          <Button className="bg-violet-600 hover:bg-violet-700">
            <Plus className="w-4 h-4 mr-2" />
            Nova campanha
          </Button>
        </Link>
      </div>

      <Card className="border-dashed border-border/50">
        <CardContent className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-4">
            <TrendingUp className="w-7 h-7 text-blue-400" />
          </div>
          <h3 className="font-semibold text-foreground">Nenhuma campanha ainda</h3>
          <p className="text-sm text-muted-foreground mt-2 max-w-sm">
            Converse com o Gestor de Tráfego para criar sua primeira campanha no Meta Ads ou Google Ads.
          </p>
          <Link href="/agents/traffic-manager" className="mt-6">
            <Button variant="outline" size="sm">
              Criar com IA
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
